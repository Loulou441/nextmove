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
    
    /// Extracts frames from a video file at the specified frame rate.
    ///
    /// PULL-BASED (backpressure-correct): returns a `VideoFrameStream` that decodes
    /// the NEXT sampled frame only when the consumer asks for it. This is a
    /// deliberate rewrite of a previous `AsyncStream(bufferingPolicy:.bufferingNewest(1))`
    /// implementation, whose `yield` never suspended the producer — so when
    /// detection was slow, the decoder raced ahead and the 1-slot buffer SILENTLY
    /// DROPPED almost every frame (observed: 2 of ~2631 frames survived → no
    /// rallies). Pulling one frame at a time guarantees no frame is ever dropped,
    /// regardless of how slow detection is, while keeping peak memory at ~one frame.
    ///
    /// - Parameters:
    ///   - url: URL of the video file (MP4, MOV, or M4V)
    ///   - frameRate: Desired frame rate (1-30 fps, default 5 fps)
    /// - Returns: A pull-based `VideoFrameStream` of video frames with metadata
    /// - Throws: VideoProcessingError if extraction fails
    /// Validates: Requirements 1.1, 1.2, 1.4, 1.5, 1.6, 1.7
    func extractFrames(from url: URL, frameRate: Int) async throws -> VideoFrameStream {
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

        // Set up the reader up-front; frames are pulled lazily by the sequence.
        let reader = try AVAssetReader(asset: asset)
        let outputSettings: [String: Any] = [
            kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA,
            kCVPixelBufferIOSurfacePropertiesKey as String: [:]
        ]
        let readerOutput = AVAssetReaderTrackOutput(track: videoTrack, outputSettings: outputSettings)
        readerOutput.alwaysCopiesSampleData = false

        guard reader.canAdd(readerOutput) else {
            throw VideoProcessingError.frameExtractionFailed(reason: "Cannot add reader output")
        }
        reader.add(readerOutput)

        let nominalFrameRate = try await videoTrack.load(.nominalFrameRate)
        let frameInterval = calculateFrameInterval(
            desiredFrameRate: validatedFrameRate,
            nominalFrameRate: nominalFrameRate
        )

        guard reader.startReading() else {
            let reason = reader.error?.localizedDescription ?? "Failed to start reading"
            throw VideoProcessingError.frameExtractionFailed(reason: reason)
        }

        // Pull-based: each call decodes exactly one sampled frame on demand.
        // Per-iterator mutable state (lastProcessedTime, frameNumber) is captured
        // in the closure so it survives across pulls without being shared.
        return VideoFrameStream { [weak self] in
            var lastProcessedTime = CMTime.zero
            var frameNumber = 0
            return {
                guard let self else { return nil }
                let frame = self.nextFrame(
                    output: readerOutput,
                    reader: reader,
                    frameInterval: frameInterval,
                    lastProcessedTime: &lastProcessedTime,
                    frameNumber: frameNumber
                )
                if frame != nil { frameNumber += 1 }
                return frame
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
    
    /// Pulls the next sampled frame from the reader, applying frame-rate
    /// downsampling. Returns nil when the video is exhausted. Called one frame at
    /// a time by `VideoFrameStream`, so the decoder never runs ahead of detection.
    /// `frameNumber` is the index among YIELDED frames (0,1,2,…) — contiguous,
    /// which is what the tracker relies on for its frame-gap logic.
    fileprivate func nextFrame(
        output: AVAssetReaderTrackOutput,
        reader: AVAssetReader,
        frameInterval: CMTime,
        lastProcessedTime: inout CMTime,
        frameNumber: Int
    ) -> VideoFrame? {
        while reader.status == .reading {
            if isCancelled { reader.cancelReading(); return nil }

            // autoreleasepool so the CMSampleBuffer/CIImage temporaries are freed
            // each iteration rather than accumulating (a key OOM cause).
            let outcome: FrameOutcome = autoreleasepool {
                guard let sampleBuffer = output.copyNextSampleBuffer() else {
                    return .end
                }
                let presentationTime = CMSampleBufferGetPresentationTimeStamp(sampleBuffer)

                guard shouldProcessFrame(
                    currentTime: presentationTime,
                    lastProcessedTime: lastProcessedTime,
                    frameInterval: frameInterval
                ) else {
                    return .skip  // frame-rate downsampling — keep reading
                }

                guard let cgImage = createCGImage(from: sampleBuffer) else {
                    return .skip
                }
                lastProcessedTime = presentationTime
                return .frame(VideoFrame(image: cgImage, timestamp: presentationTime, frameNumber: frameNumber))
            }

            switch outcome {
            case .frame(let f): return f
            case .skip:         continue
            case .end:          return nil
            }
        }
        return nil
    }

    /// Result of attempting to pull one frame from the reader.
    private enum FrameOutcome {
        case frame(VideoFrame)
        case skip
        case end
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


