//
//  CameraRecorder.swift
//  nextmove
//
//  Real in-app video recording via AVFoundation. Replaces the old placeholder
//  "camera preview" (a grey rectangle) that produced no actual file — which is
//  why recorded games showed black and had no video to analyse.
//
//  Provides:
//   • CameraRecorder — manages an AVCaptureSession (camera + mic → movie file)
//   • CameraPreview  — a SwiftUI wrapper around AVCaptureVideoPreviewLayer
//
//  NOTE: the camera only works on a PHYSICAL device, not the Simulator.
//

import Foundation
import AVFoundation
import SwiftUI
import Combine

@MainActor
final class CameraRecorder: NSObject, ObservableObject {

    /// True once the session is configured and running (preview can show).
    @Published var isReady = false
    /// True while actively writing a movie file.
    @Published var isRecording = false
    /// Set if setup/permissions failed, so the UI can explain instead of showing black.
    @Published var errorMessage: String?

    /// The capture session the preview layer renders.
    let session = AVCaptureSession()

    private let movieOutput = AVCaptureMovieFileOutput()
    private let sessionQueue = DispatchQueue(label: "com.nextmove.camera.session")
    private var didConfigure = false

    /// Called with the final file URL when a recording finishes, or nil on error.
    private var finishHandler: ((URL?) -> Void)?

    // MARK: - Permissions + setup

    /// Requests camera + mic permission and configures the session. Safe to call
    /// repeatedly (configures once). Call from the view's .task/onAppear.
    func prepare() {
        requestAccess { [weak self] granted in
            guard let self else { return }
            guard granted else {
                Task { @MainActor in self.errorMessage = "Accès caméra refusé. Activez-le dans Réglages." }
                return
            }
            self.sessionQueue.async { self.configureIfNeeded() }
        }
    }

    private func requestAccess(_ completion: @escaping (Bool) -> Void) {
        // Camera, then microphone.
        AVCaptureDevice.requestAccess(for: .video) { camOK in
            guard camOK else { completion(false); return }
            AVCaptureDevice.requestAccess(for: .audio) { _ in
                // Mic denial shouldn't block video; proceed either way.
                completion(true)
            }
        }
    }

    private func configureIfNeeded() {
        guard !didConfigure else { return }
        session.beginConfiguration()
        session.sessionPreset = .high

        // Video input (back camera).
        if let camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back),
           let videoInput = try? AVCaptureDeviceInput(device: camera),
           session.canAddInput(videoInput) {
            session.addInput(videoInput)
        } else {
            session.commitConfiguration()
            Task { @MainActor in self.errorMessage = "Caméra indisponible sur cet appareil." }
            return
        }

        // Audio input (optional).
        if let mic = AVCaptureDevice.default(for: .audio),
           let audioInput = try? AVCaptureDeviceInput(device: mic),
           session.canAddInput(audioInput) {
            session.addInput(audioInput)
        }

        // Movie file output.
        if session.canAddOutput(movieOutput) {
            session.addOutput(movieOutput)
        }

        session.commitConfiguration()
        didConfigure = true

        session.startRunning()
        Task { @MainActor in self.isReady = true }
    }

    // MARK: - Recording

    /// Starts recording to a fresh file in the app's Documents directory.
    func startRecording() {
        sessionQueue.async { [weak self] in
            guard let self, self.didConfigure, !self.movieOutput.isRecording else { return }
            let url = FileManager.default
                .urls(for: .documentDirectory, in: .userDomainMask)[0]
                .appendingPathComponent("\(UUID().uuidString).mov")
            self.movieOutput.startRecording(to: url, recordingDelegate: self)
            Task { @MainActor in self.isRecording = true }
        }
    }

    /// Stops recording; `completion` receives the saved file URL (or nil).
    func stopRecording(completion: @escaping (URL?) -> Void) {
        sessionQueue.async { [weak self] in
            guard let self, self.movieOutput.isRecording else {
                Task { @MainActor in completion(nil) }
                return
            }
            self.finishHandler = completion
            self.movieOutput.stopRecording()
        }
    }

    /// Stops the session (call when leaving the screen) to release the camera.
    func stop() {
        sessionQueue.async { [weak self] in
            guard let self, self.session.isRunning else { return }
            self.session.stopRunning()
        }
    }
}

// MARK: - Recording delegate

extension CameraRecorder: AVCaptureFileOutputRecordingDelegate {
    nonisolated func fileOutput(_ output: AVCaptureFileOutput,
                                didFinishRecordingTo outputFileURL: URL,
                                from connections: [AVCaptureConnection],
                                error: Error?) {
        Task { @MainActor in
            self.isRecording = false
            let handler = self.finishHandler
            self.finishHandler = nil
            if let error {
                self.errorMessage = "Enregistrement échoué : \(error.localizedDescription)"
                handler?(nil)
            } else {
                handler?(outputFileURL)
            }
        }
    }
}

// MARK: - SwiftUI preview wrapper

/// Shows the live camera feed by hosting an AVCaptureVideoPreviewLayer.
struct CameraPreview: UIViewRepresentable {
    let session: AVCaptureSession

    func makeUIView(context: Context) -> PreviewView {
        let view = PreviewView()
        view.videoPreviewLayer.session = session
        view.videoPreviewLayer.videoGravity = .resizeAspectFill
        return view
    }

    func updateUIView(_ uiView: PreviewView, context: Context) {
        uiView.videoPreviewLayer.session = session
    }

    /// A UIView whose backing layer IS the preview layer (so it resizes cleanly).
    final class PreviewView: UIView {
        override class var layerClass: AnyClass { AVCaptureVideoPreviewLayer.self }
        var videoPreviewLayer: AVCaptureVideoPreviewLayer {
            layer as! AVCaptureVideoPreviewLayer
        }
    }
}
