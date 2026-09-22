//
//  RecordingViewModel.swift
//  nextmove
//

import Foundation
import AVFoundation
import SwiftUI
import CoreMedia
import Combine

@MainActor
class RecordingViewModel: ObservableObject {
    let objectWillChange = ObservableObjectPublisher()

    @Published var recordings: [GameRecording] = []
    @Published var isRecording = false
    @Published var isProcessing = false
    @Published var selectedRecording: GameRecording? = nil

    @Published var analysisProgress: String = ""
    @Published var analysisProgressPercentage: Double = 0.0
    @Published var analysisError: String?

    private let storageKey = "savedRecordings"

    init() {
        loadRecordings()
    }

    // MARK: - Recordings Management

    func addRecording(videoURL: URL, title: String, sportType: SportType = .pickleball) {
        let recording = GameRecording(title: title, videoURL: videoURL, duration: getVideoDuration(url: videoURL), sportType: sportType)
        recordings.insert(recording, at: 0)
        objectWillChange.send()
        saveRecordings()
    }

    func recordings(for sport: SportType) -> [GameRecording] {
        recordings.filter { $0.sportType == sport }
    }

    func deleteRecording(_ recording: GameRecording) {
        recordings.removeAll { $0.id == recording.id }
        if let url = recording.videoURL {
            try? FileManager.default.removeItem(at: url)
        }
        saveRecordings()
    }

    func deleteAllRecordings() {
        for recording in recordings {
            if let url = recording.videoURL {
                try? FileManager.default.removeItem(at: url)
            }
        }
        recordings.removeAll()
        saveRecordings()
    }

    // MARK: - Analysis

    /// Set to false to force demo mode (mock analysis) regardless of model availability.
    private let useRealAnalysis = true

    /// TEMPORARY DEBUG: when true, real-analysis failures surface as an on-screen
    /// error instead of silently falling back to demo. Set back to false for the
    /// graceful demo fallback once diagnosis is done.
    private let showRealAnalysisErrors = true

    func processRecording(_ recording: GameRecording) async {
        guard let index = recordings.firstIndex(where: { $0.id == recording.id }) else { return }

        print("\n========================================")
        print("🎬 ANALYZE tapped for: \(recording.title)")
        print("   useRealAnalysis = \(useRealAnalysis)")
        print("========================================")

        recordings[index].status = .processing
        isProcessing = true
        analysisError = nil
        analysisProgress = "Initializing analysis..."
        analysisProgressPercentage = 0.0

        if useRealAnalysis {
            let succeeded = await runRealAnalysis(at: index)
            if succeeded {
                print("✅✅✅ RESULT: REAL on-device analysis was used")
                return
            }
            if showRealAnalysisErrors {
                // Debug mode: stop here so the on-screen error is visible.
                print("🛑 RESULT: real analysis failed — showing error on screen (demo fallback suppressed for debugging)")
                return
            }
            // Real analysis failed — fall back to demo so the app always produces a result.
            print("⚠️⚠️⚠️ RESULT: FELL BACK TO DEMO (real analysis failed above)")
            await MainActor.run {
                analysisProgress = "Finalizing analysis..."
                analysisProgressPercentage = 0.0
            }
        } else {
            print("⚠️ RESULT: DEMO mode (useRealAnalysis is off)")
        }

        await runDemoAnalysis(at: index)
    }

    func retryAnalysis(_ recording: GameRecording) async {
        await processRecording(recording)
    }

    // MARK: - Real CV/ML Analysis

    /// Runs the real on-device analysis pipeline against the trained Core ML model.
    /// Returns true on success, false if it should fall back to demo mode.
    private func runRealAnalysis(at index: Int) async -> Bool {
        let recording = recordings[index]

        // Verify the model is actually in the bundle before we start.
        if Bundle.main.url(forResource: "PickleballDetector_v1", withExtension: "mlpackage") == nil
            && Bundle.main.url(forResource: "PickleballDetector_v1", withExtension: "mlmodelc") == nil {
            print("🔍 BUNDLE CHECK: PickleballDetector_v1 NOT found at bundle root (may still be in a subdir; ModelManager will scan).")
        } else {
            print("🔍 BUNDLE CHECK: PickleballDetector_v1 IS present in bundle.")
        }

        let modelManager = ModelManager()
        let pipeline = AnalysisPipeline.withLLMCoaching(
            videoProcessor: VideoProcessor(),
            objectDetector: ObjectDetector(modelManager: modelManager),
            objectTracker: ObjectTracker(),
            featureExtractor: FeatureExtractor(),
            modelManager: modelManager,
            useLLM: true  // Falls back to rule-based coaching if no API key
        )

        // Stream progress updates into the UI.
        let progressTask = Task {
            for await progress in pipeline.progress {
                await MainActor.run {
                    self.analysisProgress = progress.message
                    self.analysisProgressPercentage = progress.percentage
                }
            }
        }

        do {
            let analysis = try await pipeline.analyze(
                recording: recording,
                sportType: recording.sportType
            )
            await progressTask.value

            await MainActor.run {
                if let i = self.recordings.firstIndex(where: { $0.id == recording.id }) {
                    self.recordings[i].analysis = analysis
                    self.recordings[i].status = .completed
                }
                self.analysisProgress = "Analysis complete!"
                self.analysisProgressPercentage = 1.0
                self.isProcessing = false
                self.saveRecordings()
            }
            return true

        } catch {
            progressTask.cancel()
            // Log the real reason; the caller will fall back to demo mode.
            print("❌ Real analysis failed: \(error)")
            print("   localizedDescription: \(error.localizedDescription)")

            // DEBUG: surface the failure on screen so it doesn't hide behind demo data.
            if showRealAnalysisErrors {
                await MainActor.run {
                    if let i = self.recordings.firstIndex(where: { $0.id == recording.id }) {
                        self.recordings[i].status = .failed
                    }
                    self.analysisError = "Real analysis failed: \(error.localizedDescription)"
                    self.analysisProgress = "Analysis failed"
                    self.isProcessing = false
                    self.saveRecordings()
                }
            }
            return false
        }
    }

    // MARK: - Demo Analysis

    private func runDemoAnalysis(at index: Int) async {
        let stages: [(Double, String)] = [
            (0.20, "Extracting frames from video..."),
            (0.40, "Detecting objects in frames..."),
            (0.60, "Tracking objects across frames..."),
            (0.80, "Extracting performance metrics..."),
            (0.95, "Generating coaching feedback...")
        ]

        for (pct, msg) in stages {
            analysisProgress = msg
            analysisProgressPercentage = pct
            try? await Task.sleep(nanoseconds: 700_000_000)
        }

        let mockAnalysis = makeMockAnalysis()

        recordings[index].analysis = mockAnalysis
        recordings[index].status = .completed
        analysisProgress = "Analysis complete!"
        analysisProgressPercentage = 1.0
        isProcessing = false
        saveRecordings()
    }

    private func makeMockAnalysis() -> GameAnalysis {
        let skillRatings = GameAnalysis.SkillRatings(
            serve: Double.random(in: 3.2...4.6),
            return: Double.random(in: 3.0...4.5),
            thirdShot: Double.random(in: 2.8...4.2),
            dinking: Double.random(in: 3.5...4.8),
            volleys: Double.random(in: 3.3...4.7),
            movement: Double.random(in: 3.4...4.6)
        )

        let totalRallies = Int.random(in: 48...72)
        let winners = Int.random(in: 14...24)
        let errors = Int.random(in: 8...16)
        let attacks = Int.random(in: 20...32)

        let statistics = GameAnalysis.GameStatistics(
            totalRallies: totalRallies,
            longestRally: Int.random(in: 18...30),
            winners: winners,
            errors: errors,
            attacksAttempted: attacks,
            attacksSuccessful: Int(Double(attacks) * Double.random(in: 0.55...0.75)),
            courtCoveragePercent: Double.random(in: 68...84)
        )

        let highlights = [
            GameAnalysis.Highlight(type: .winner,       timestamp: 42,  duration: 5,  description: "Powerful cross-court winner"),
            GameAnalysis.Highlight(type: .longRally,    timestamp: 97,  duration: 18, description: "24-shot rally with excellent dinking"),
            GameAnalysis.Highlight(type: .attack,       timestamp: 163, duration: 4,  description: "Aggressive third shot drive"),
            GameAnalysis.Highlight(type: .greatDefense, timestamp: 218, duration: 6,  description: "Amazing defensive lob recovery")
        ]

        let heatMap = GameAnalysis.CourtHeatMap(
            positions: (0..<60).map { _ in
                GameAnalysis.CourtHeatMap.CourtPosition(
                    x: Double.random(in: 0.15...0.85),
                    y: Double.random(in: 0.35...0.90),
                    intensity: Double.random(in: 0.4...1.0)
                )
            }
        )

        let overall = (skillRatings.serve + skillRatings.return + skillRatings.thirdShot +
                       skillRatings.dinking + skillRatings.volleys + skillRatings.movement) / 6.0

        return GameAnalysis(
            overallRating: overall,
            skillRatings: skillRatings,
            statistics: statistics,
            highlights: highlights,
            heatMap: heatMap
        )
    }

    // MARK: - Helpers

    private func getVideoDuration(url: URL) -> TimeInterval {
        let asset = AVURLAsset(url: url)
        return CMTimeGetSeconds(asset.duration)
    }

    private func saveRecordings() {
        if let encoded = try? JSONEncoder().encode(recordings) {
            UserDefaults.standard.set(encoded, forKey: storageKey)
        }
    }

    private func loadRecordings() {
        if let data = UserDefaults.standard.data(forKey: storageKey),
           let decoded = try? JSONDecoder().decode([GameRecording].self, from: data) {
            recordings = decoded
        }
    }
}
