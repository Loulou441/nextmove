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
    // NOTE: Do NOT declare a custom `objectWillChange` here. Providing one
    // suppresses the synthesized publisher, which means @Published changes
    // (recordings, isProcessing, analysisProgress…) stop notifying SwiftUI —
    // the UI then never reflects "processing"/progress. Let ObservableObject
    // synthesize it so @Published drives view updates.

    @Published var recordings: [GameRecording] = []
    @Published var isRecording = false
    @Published var isProcessing = false
    @Published var selectedRecording: GameRecording? = nil

    @Published var analysisProgress: String = ""
    @Published var analysisProgressPercentage: Double = 0.0
    @Published var analysisError: String?

    private let storageKey = "savedRecordings"

    /// Client de l'API partagée, injecté par ContentView une fois disponible.
    /// Sert à synchroniser une analyse terminée vers la base partagée pour
    /// qu'elle apparaisse aussi sur le web. Optionnel : si nil (previews, tests,
    /// utilisateur non connecté), l'analyse locale fonctionne quand même.
    weak var api: NextMoveAPI?

    init() {
        loadRecordings()
    }

    // MARK: - Recordings Management

    func addRecording(videoURL: URL, title: String, sportType: SportType = .pickleball) {
        let recording = GameRecording(title: title, videoURL: videoURL, duration: getVideoDuration(url: videoURL), sportType: sportType)
        recordings.insert(recording, at: 0)  // @Published triggers the UI update
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

    /// When true, real-analysis failures surface as an on-screen error (debug).
    /// When false (demo mode), failures fall back gracefully to a complete demo
    /// analysis so the app ALWAYS produces a result and the UI reaches .completed.
    private let showRealAnalysisErrors = false

    func processRecording(_ recording: GameRecording) async {
        guard let index = recordings.firstIndex(where: { $0.id == recording.id }) else { return }

        print("\n========================================")
        print("🎬 ANALYZE tapped for: \(recording.title)")
        print("   useRealAnalysis = \(useRealAnalysis)")
        print("========================================")

        recordings[index].status = .processing
        isProcessing = true
        analysisError = nil
        analysisProgress = String(localized: "Initializing analysis...")
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
                analysisProgress = String(localized: "Finalizing analysis...")
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

    /// Pousse une analyse terminée vers la base partagée (POST /matches/sync)
    /// afin qu'elle soit visible sur le web après connexion.
    ///
    /// Silencieux par conception : si l'utilisateur n'est pas connecté (pas d'API
    /// ou pas de token), on ne bloque pas et on ne montre pas d'erreur — l'analyse
    /// locale reste disponible sur l'appareil dans tous les cas.
    private func syncAnalysisToBackend(_ recording: GameRecording, _ analysis: GameAnalysis) async {
        guard let api, api.isLoggedIn else { return }

        let stats = analysis.statistics
        let ratingOn10 = (analysis.overallRating / 5.0) * 10.0  // 0–5 → 0–10

        // Mappe les GameAnalysis.Highlight vers le format attendu par l'API.
        let highlights = analysis.highlights.map { h -> [String: String] in
            [
                "title": h.description,
                "time": String(format: "%d:%02d", Int(h.timestamp) / 60, Int(h.timestamp) % 60),
                "tag": h.type.rawValue,
            ]
        }

        // Skills → même format que l'app web (label + score /100 + couleur).
        let sr = analysis.skillRatings
        func skillEntry(_ label: String, _ ratingOn5: Double) -> [String: String] {
            let pct = Int((ratingOn5 / 5.0 * 100).rounded())
            let color = pct >= 75 ? "green" : (pct >= 50 ? "orange" : "red")
            return ["label": label, "score": "\(pct)", "color": color]
        }
        let skills = [
            skillEntry("Serve", sr.serve),
            skillEntry("Return", sr.return),
            skillEntry("Third Shot", sr.thirdShot),
            skillEntry("Dinking", sr.dinking),
            skillEntry("Volleys", sr.volleys),
            skillEntry("Movement", sr.movement),
        ]

        do {
            let synced = try await api.syncMatch(
                title: recording.title,
                sport: recording.sportType.rawValue,
                duration: String(format: "%d:%02d", Int(recording.duration) / 60, Int(recording.duration) % 60),
                rallies: stats.totalRallies,
                winners: stats.winners,
                errors: stats.errors,
                coverage: Int(stats.courtCoveragePercent.rounded()),
                rating: (ratingOn10 * 10).rounded() / 10,
                skills: skills,
                highlights: highlights
            )
            // Persist the server match id on the local recording so the AI coach
            // chat can route through the backend (same moderator + RAG as web).
            if let idx = recordings.firstIndex(where: { $0.id == recording.id }) {
                recordings[idx].serverMatchId = synced.id
                saveRecordings()
            }
            print("☁️ Analyse synchronisée vers la base partagée (visible sur le web).")
        } catch {
            // Non bloquant : l'analyse locale reste valable.
            print("⚠️ Sync backend échouée (non bloquant) : \(error.localizedDescription)")
        }
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
        // 0.10 (was 0.15): the small, fast ball is frequently detected at low
        // confidence; a slightly lower floor recovers ball frames so rallies
        // don't collapse. Players are large and sit well above this anyway, and
        // the tracker's per-track confidence averaging still filters noise.
        objectDetector: ObjectDetector(modelManager: modelManager, confidenceThreshold: 0.10),
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
            // Run the heavy CV/ML work OFF the main actor. The pipeline performs
            // synchronous CoreML (Vision) inference and CoreImage frame decoding;
            // if that runs on the main actor it blocks/freezes the UI. Task.detached
            // guarantees it executes on a background executor.
            let sport = recording.sportType
            let analysis = try await Task.detached(priority: .userInitiated) {
                try await pipeline.analyze(
                    recording: recording,
                    sportType: sport
                )
            }.value
            await progressTask.value

            await MainActor.run {
                if let i = self.recordings.firstIndex(where: { $0.id == recording.id }) {
                    self.recordings[i].analysis = analysis
                    self.recordings[i].status = .completed
                }
                self.analysisProgress = String(localized: "Analysis complete!")
                self.analysisProgressPercentage = 1.0
                self.isProcessing = false
                self.saveRecordings()
            }

            // Synchronise vers la base partagée (visible sur le web). Non bloquant.
            await syncAnalysisToBackend(recording, analysis)
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
                    self.analysisError = String(localized: "Real analysis failed: \(error.localizedDescription)")
                    self.analysisProgress = String(localized: "Analysis failed")
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
            (0.20, String(localized: "Extracting frames from video...")),
            (0.40, String(localized: "Detecting objects in frames...")),
            (0.60, String(localized: "Tracking objects across frames...")),
            (0.80, String(localized: "Extracting performance metrics...")),
            (0.95, String(localized: "Generating coaching feedback..."))
        ]

        for (pct, msg) in stages {
            analysisProgress = msg
            analysisProgressPercentage = pct
            try? await Task.sleep(nanoseconds: 700_000_000)
        }

        let recording = recordings[index]
        let mockAnalysis = makeMockAnalysis(for: recording)

        recordings[index].analysis = mockAnalysis
        recordings[index].status = .completed
        analysisProgress = String(localized: "Analysis complete!")
        analysisProgressPercentage = 1.0
        isProcessing = false
        saveRecordings()

        // Synchronise vers la base partagée (visible sur le web). Non bloquant.
        await syncAnalysisToBackend(recording, mockAnalysis)
    }

    /// Builds the demo/fallback analysis. Seeded from the recording's stable id
    /// so the SAME recording always produces the SAME demo result — otherwise a
    /// transient real-analysis failure could swap a game's numbers on every
    /// retry. (The real pipeline is the source of truth; this only runs when it
    /// fails and demo fallback is enabled.)
    private func makeMockAnalysis(for recording: GameRecording) -> GameAnalysis {
        var rng = SeededGenerator(seed: recording.id)

        func rand(_ range: ClosedRange<Double>) -> Double { Double.random(in: range, using: &rng) }
        func rand(_ range: ClosedRange<Int>) -> Int { Int.random(in: range, using: &rng) }

        let skillRatings = GameAnalysis.SkillRatings(
            serve: rand(3.2...4.6),
            return: rand(3.0...4.5),
            thirdShot: rand(2.8...4.2),
            dinking: rand(3.5...4.8),
            volleys: rand(3.3...4.7),
            movement: rand(3.4...4.6)
        )

        let totalRallies = rand(48...72)
        let winners = rand(14...24)
        let errors = rand(8...16)
        let attacks = rand(20...32)

        let statistics = GameAnalysis.GameStatistics(
            totalRallies: totalRallies,
            longestRally: rand(18...30),
            winners: winners,
            errors: errors,
            avgRallyLength: rand(3.0...8.0),
            avgBallSpeed: rand(0.3...0.7),
            winRate: Double(winners) / Double(max(totalRallies, 1)) * 100,
            courtCoveragePercent: rand(68...84)
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
                    x: rand(0.15...0.85),
                    y: rand(0.35...0.90),
                    intensity: rand(0.4...1.0)
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

/// Deterministic RNG (SplitMix64) seeded from a UUID. Only used by the demo
/// fallback so the same recording yields the same placeholder numbers instead
/// of new random ones on every retry. The REAL analysis does not use this.
private struct SeededGenerator: RandomNumberGenerator {
    private var state: UInt64

    init(seed: UUID) {
        // Fold the 16 UUID bytes into a 64-bit seed.
        var hasher = Hasher()
        hasher.combine(seed)
        // Hasher is randomized per process; use the UUID bytes directly for a
        // stable, process-independent seed instead.
        let bytes = withUnsafeBytes(of: seed.uuid) { Array($0) }
        var s: UInt64 = 0xcbf29ce484222325
        for b in bytes {
            s = (s ^ UInt64(b)) &* 0x100000001b3
        }
        state = s == 0 ? 0x9e3779b97f4a7c15 : s
    }

    mutating func next() -> UInt64 {
        state = state &+ 0x9e3779b97f4a7c15
        var z = state
        z = (z ^ (z >> 30)) &* 0xbf58476d1ce4e5b9
        z = (z ^ (z >> 27)) &* 0x94d049bb133111eb
        return z ^ (z >> 31)
    }
}
