//
//  VideoProcessor.swift
//  nextmove
//
//  Extracts frames from video files using AVFoundation
//  Validates: Requirements 1.1-1.7, 14.6
//

import Foundation
import AVFoundation
import CoreGraphics
import CoreMedia
import CoreImage

/// VideoProcessor extracts frames from video files at configurable frame rates
/// Uses AVAssetReader for memory-efficient frame extraction via AsyncStream
/// Validates: Requirements 1.1-1.7, 14.6
final class VideoProcessor: VideoProcessorProtocol {
    
    // MARK: - Properties
    
    private var isCancelled = false

    /// Reused across all frames. Creating a CIContext per frame is very expensive
    /// (allocates Metal/GPU resources each time) and was a major source of the
    /// memory blowup — create it once and reuse it.
    private lazy var ciContext = CIContext(options: [.useSoftwareRenderer: false])

    /// Frames are downscaled so their long side is at most this many pixels before
    /// detection. Keeps per-frame memory small; the model input is smaller anyway.
    private let maxFrameDimension: CGFloat = 960
    private let supportedFormats: Set<String> = ["mp4", "mov", "m4v"]
    private let maxDuration: TimeInterval = 60 * 60 // 60 minutes
    private let minFrameRate = 1
    private let maxFrameRate = 30
    private let defaultFrameRate = 5
    
    // MARK: - Initialization
    
    init() {}
    
    // MARK: - VideoProcessorProtocol
    
    /// Extracts frames from a video file at the specified frame rate
    /// - Parameters:
    ///   - url: URL of the video file (MP4, MOV, or M4V)
    ///   - frameRate: Desired frame rate (1-30 fps, default 5 fps)
    /// - Returns: AsyncStream of video frames with timestamps and metadata
    /// - Throws: VideoProcessingError if extraction fails
    /// Validates: Requirements 1.1, 1.2, 1.4, 1.5, 1.6, 1.7
    func extractFrames(from url: URL, frameRate: Int) async throws -> AsyncStream<VideoFrame> {
        // Validate frame rate
        let validatedFrameRate = validateFrameRate(frameRate)
        
        // Validate video file exists
        guard FileManager.default.fileExists(atPath: url.path) else {
            throw VideoProcessingError.fileNotFound
        }
        
        // Validate video format
        let fileExtension = url.pathExtension.lowercased()
        guard supportedFormats.contains(fileExtension) else {
            throw VideoProcessingError.invalidVideoFormat
        }
        
        // Create AVAsset and validate
        let asset = AVAsset(url: url)
        try await validateAsset(asset)
        
        // Get video track
        guard let videoTrack = try await asset.loadTracks(withMediaType: .video).first else {
            throw VideoProcessingError.frameExtractionFailed(reason: "No video track found")
        }
        
        // Bounded buffer (keep only the newest pending frame) so the decoder
        // CANNOT run ahead of the detector. Without this, the AsyncStream's default
        // unbounded buffer queues hundreds of full-resolution CGImages faster than
        // detection drains them → out-of-memory crash. bufferingNewest(1) applies
        // backpressure: at most one frame is in flight at a time.
        return AsyncStream(bufferingPolicy: .bufferingNewest(1)) { continuation in
            Task {
                do {
                    try await self.processFrames(
                        from: asset,
                        videoTrack: videoTrack,
                        frameRate: validatedFrameRate,
                        continuation: continuation
                    )
                    continuation.finish()
                } catch {
                    continuation.finish()
                    throw error
                }
            }
        }
    }
    
    // MARK: - Private Methods
    
    /// Validates and clamps frame rate to supported range
    private func validateFrameRate(_ frameRate: Int) -> Int {
        return max(minFrameRate, min(frameRate, maxFrameRate))
    }
    
    /// Validates asset duration and readability
    private func validateAsset(_ asset: AVAsset) async throws {
        // Check if asset is readable
        let isReadable = try await asset.load(.isReadable)
        guard isReadable else {
            throw VideoProcessingError.frameExtractionFailed(reason: "Video file is not readable")
        }
        
        // Validate duration
        let duration = try await asset.load(.duration)
        guard duration.isValid && !duration.isIndefinite else {
            throw VideoProcessingError.frameExtractionFailed(reason: "Invalid video duration")
        }
        
        let durationSeconds = duration.seconds
        guard durationSeconds > 0 && durationSeconds <= maxDuration else {
            throw VideoProcessingError.unsupportedDuration
        }
    }
    
    /// Processes frames from the video asset
    private func processFrames(
        from asset: AVAsset,
        videoTrack: AVAssetTrack,
        frameRate: Int,
        continuation: AsyncStream<VideoFrame>.Continuation
    ) async throws {
        // Create asset reader
        let reader = try AVAssetReader(asset: asset)
        
        // Configure output settings for frame extraction
        let outputSettings: [String: Any] = [
            kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA,
            kCVPixelBufferIOSurfacePropertiesKey as String: [:]
        ]
        
        let readerOutput = AVAssetReaderTrackOutput(
            track: videoTrack,
            outputSettings: outputSettings
        )
        readerOutput.alwaysCopiesSampleData = false // Memory optimization
        
        guard reader.canAdd(readerOutput) else {
            throw VideoProcessingError.frameExtractionFailed(reason: "Cannot add reader output")
        }
        
        reader.add(readerOutput)
        
        // Calculate frame interval based on desired frame rate
        let duration = try await asset.load(.duration)
        let nominalFrameRate = try await videoTrack.load(.nominalFrameRate)
        let frameInterval = calculateFrameInterval(
            desiredFrameRate: frameRate,
            nominalFrameRate: nominalFrameRate
        )
        
        // Start reading
        guard reader.startReading() else {
            if let error = reader.error {
                throw VideoProcessingError.frameExtractionFailed(reason: error.localizedDescription)
            }
            throw VideoProcessingError.frameExtractionFailed(reason: "Failed to start reading")
        }
        
        // Process frames on background queue
        var frameNumber = 0
        var lastProcessedTime = CMTime.zero
        
        var reachedEnd = false
        while reader.status == .reading && !reachedEnd {
            // Check for cancellation
            if isCancelled {
                reader.cancelReading()
                break
            }

            // Decode + convert inside an autorelease pool so the CMSampleBuffer,
            // CIImage and other temporaries are freed EVERY iteration rather than
            // accumulating for the lifetime of the loop (a key OOM cause).
            // Returns the produced frame (if any); sets reachedEnd when the reader
            // has no more sample buffers.
            let produced: VideoFrame? = autoreleasepool {
                guard let sampleBuffer = readerOutput.copyNextSampleBuffer() else {
                    reachedEnd = true
                    return nil
                }
                let presentationTime = CMSampleBufferGetPresentationTimeStamp(sampleBuffer)

                guard shouldProcessFrame(
                    currentTime: presentationTime,
                    lastProcessedTime: lastProcessedTime,
                    frameInterval: frameInterval
                ) else {
                    return nil  // skip this frame (frame-rate downsampling), keep reading
                }

                guard let cgImage = createCGImage(from: sampleBuffer) else {
                    return nil
                }
                lastProcessedTime = presentationTime
                return VideoFrame(image: cgImage, timestamp: presentationTime, frameNumber: frameNumber)
            }

            if let frame = produced {
                // Suspends here until the consumer is ready (bounded buffer applies
                // backpressure), so the decoder can't outrun detection.
                continuation.yield(frame)
                frameNumber += 1
            }
        }
        
        // Check for errors
        if reader.status == .failed {
            if let error = reader.error {
                throw VideoProcessingError.frameExtractionFailed(reason: error.localizedDescription)
            }
        }
    }
    
    /// Calculates the time interval between frames based on desired frame rate
    private func calculateFrameInterval(desiredFrameRate: Int, nominalFrameRate: Float) -> CMTime {
        let interval = 1.0 / Double(desiredFrameRate)
        return CMTime(seconds: interval, preferredTimescale: 600)
    }
    
    /// Determines if a frame should be processed based on frame rate
    private func shouldProcessFrame(
        currentTime: CMTime,
        lastProcessedTime: CMTime,
        frameInterval: CMTime
    ) -> Bool {
        if lastProcessedTime == CMTime.zero {
            return true // Always process first frame
        }
        
        let timeSinceLastFrame = CMTimeSubtract(currentTime, lastProcessedTime)
        return timeSinceLastFrame >= frameInterval
    }
    
    /// Creates a CGImage from a sample buffer
    private func createCGImage(from sampleBuffer: CMSampleBuffer) -> CGImage? {
        guard let imageBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else {
            return nil
        }
        
        CVPixelBufferLockBaseAddress(imageBuffer, .readOnly)
        defer {
            CVPixelBufferUnlockBaseAddress(imageBuffer, .readOnly)
        }
        
        let sourceImage = CIImage(cvPixelBuffer: imageBuffer)

        // Downscale so the long side is at most `maxFrameDimension`. The detection
        // model runs at a fixed small input size anyway, so full-resolution frames
        // waste large amounts of memory (a 1080p/4K CGImage is 8–40 MB each) for no
        // accuracy gain. Downscaling here is the biggest per-frame memory saver.
        let extent = sourceImage.extent
        let longSide = max(extent.width, extent.height)
        let ciImage: CIImage
        if longSide > maxFrameDimension {
            let scale = maxFrameDimension / longSide
            ciImage = sourceImage.transformed(by: CGAffineTransform(scaleX: scale, y: scale))
        } else {
            ciImage = sourceImage
        }

        guard let cgImage = ciContext.createCGImage(ciImage, from: ciImage.extent) else {
            return nil
        }
        
        return cgImage
    }
    
    /// Cancels the current frame extraction operation
    func cancel() {
        isCancelled = true
    }
}
