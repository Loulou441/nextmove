//
//  PlayerSelectionView.swift
//  nextmove
//
//  "tap the player that's you" screen. Shows a thumbnail crop
//  of each detected player; tapping one scopes the stats to that person.
//
//  This is tier-2a: player identification BY SELECTION (not biometric). See
//  PlayerIdentification.swift for the honest scope note.
//

import SwiftUI
import Combine
import AVFoundation
import CoreImage
import UIKit

// MARK: - Thumbnail provider

/// Generates a cropped thumbnail for a `PlayerCandidate` by seeking the source
/// video to the candidate's best frame and cropping to its bounding box.
///
/// Vision/YOLO boxes are normalised with the ORIGIN AT TOP-LEFT and y growing
/// downward (that's how the detection pipeline stored them). `AVAsset` images
/// are also top-left origin, so we can crop directly without flipping.
enum PlayerThumbnailProvider {

    static func thumbnail(for candidate: PlayerCandidate, videoURL: URL) async -> UIImage? {
        let asset = AVURLAsset(url: videoURL)
        let generator = AVAssetImageGenerator(asset: asset)
        generator.appliesPreferredTrackTransform = true
        generator.requestedTimeToleranceBefore = .zero
        generator.requestedTimeToleranceAfter = CMTime(seconds: 0.2, preferredTimescale: 600)

        let cg: CGImage
        do {
            cg = try await generateCGImage(generator, at: candidate.thumbnailTime)
        } catch {
            return nil
        }

        let full = CGFloat(cg.width)
        let fullH = CGFloat(cg.height)

        // Expand the tight detection box a little so the crop frames the whole
        // body/head with a margin, then clamp to the image bounds.
        let box = candidate.thumbnailBoundingBox
        let padX = box.width * 0.25
        let padY = box.height * 0.20
        var cropX = (box.minX - padX) * full
        var cropY = (box.minY - padY) * fullH
        var cropW = (box.width + 2 * padX) * full
        var cropH = (box.height + 2 * padY) * fullH
        cropX = max(0, cropX); cropY = max(0, cropY)
        cropW = min(cropW, full - cropX)
        cropH = min(cropH, fullH - cropY)
        guard cropW > 1, cropH > 1 else { return UIImage(cgImage: cg) }

        let rect = CGRect(x: cropX, y: cropY, width: cropW, height: cropH)
        guard let cropped = cg.cropping(to: rect) else { return UIImage(cgImage: cg) }
        return UIImage(cgImage: cropped)
    }

    /// Bridges the completion-handler image API to async/await.
    private static func generateCGImage(_ gen: AVAssetImageGenerator, at time: CMTime) async throws -> CGImage {
        try await withCheckedThrowingContinuation { cont in
            gen.generateCGImagesAsynchronously(forTimes: [NSValue(time: time)]) { _, image, _, _, error in
                if let image = image {
                    cont.resume(returning: image)
                } else {
                    cont.resume(throwing: error ?? NSError(domain: "PlayerThumbnail", code: -1))
                }
            }
        }
    }
}

// MARK: - View model

@MainActor
final class PlayerSelectionViewModel: ObservableObject {
    @Published var candidates: [PlayerCandidate] = []
    @Published var thumbnails: [UUID: UIImage] = [:]
    @Published var selectedID: UUID?
    @Published var isLoading = true

    let videoURL: URL?

    init(candidates: [PlayerCandidate], videoURL: URL?) {
        self.videoURL = videoURL
        self.candidates = candidates
        // Default selection = the near-side player (the likely user).
        self.selectedID = candidates.first(where: { $0.isLikelyUser })?.id ?? candidates.first?.id
    }

    /// Convenience: build candidates on the fly from raw detections (e.g. tests
    /// or a re-analysis path).
    convenience init(detections: [Detection], videoURL: URL?) {
        self.init(candidates: PlayerIdentification().identifyPlayers(from: detections), videoURL: videoURL)
    }

    var selectedCandidate: PlayerCandidate? {
        guard let id = selectedID else { return nil }
        return candidates.first { $0.id == id }
    }

    var selectedStats: PlayerStats? {
        guard let c = selectedCandidate else { return nil }
        return PlayerStatsCalculator.stats(for: c)
    }

    func loadThumbnails() async {
        guard let url = videoURL else { isLoading = false; return }
        await withTaskGroup(of: (UUID, UIImage?).self) { group in
            for c in candidates {
                group.addTask { (c.id, await PlayerThumbnailProvider.thumbnail(for: c, videoURL: url)) }
            }
            for await (id, img) in group {
                if let img = img { thumbnails[id] = img }
            }
        }
        isLoading = false
    }
}

// MARK: - View

/// Shows the detected players as tappable thumbnails and a stats panel for the
/// selected one — NextMove's per-player analysis view.
struct PlayerSelectionView: View {
    @StateObject var viewModel: PlayerSelectionViewModel

    /// Preferred entry point: candidates already computed during analysis and
    /// stored on `GameAnalysis.playerCandidates`.
    init(candidates: [PlayerCandidate], videoURL: URL?) {
        _viewModel = StateObject(wrappedValue: PlayerSelectionViewModel(candidates: candidates, videoURL: videoURL))
    }

    /// Convenience for raw detections (tests / re-analysis).
    init(detections: [Detection], videoURL: URL?) {
        _viewModel = StateObject(wrappedValue: PlayerSelectionViewModel(detections: detections, videoURL: videoURL))
    }

    private let columns = [GridItem(.adaptive(minimum: 100), spacing: 12)]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("Which player are you?")
                    .font(.title2).bold()
                Text("Tap your figure. Your stats will be measured for you specifically.")
                    .font(.subheadline).foregroundStyle(.secondary)

                if viewModel.candidates.isEmpty {
                    ContentUnavailableView(
                        "No players detected",
                        systemImage: "person.slash",
                        description: Text("The clip didn't contain clear player detections to choose from.")
                    )
                } else {
                    // Make it explicit WHO the stats below belong to.
                    if let selected = viewModel.selectedCandidate {
                        Text("Showing stats for \(selected.displayName) (\(selected.courtLabel))")
                            .font(.footnote).bold()
                            .foregroundStyle(.tint)
                    }
                    LazyVGrid(columns: columns, spacing: 12) {
                        ForEach(viewModel.candidates) { candidate in
                            PlayerThumbCell(
                                candidate: candidate,
                                image: viewModel.thumbnails[candidate.id],
                                isSelected: candidate.id == viewModel.selectedID
                            )
                            .onTapGesture { viewModel.selectedID = candidate.id }
                        }
                    }

                    if let stats = viewModel.selectedStats,
                       let candidate = viewModel.selectedCandidate {
                        PlayerStatsPanel(candidate: candidate, stats: stats)
                            // Tie the panel's identity to the selected player so
                            // SwiftUI rebuilds it (not just diffs it) on every
                            // selection change — guarantees the numbers refresh.
                            .id(candidate.id)
                            .transition(.opacity)
                    }
                }

                // Honest caveat — keep this visible.
                Text("Player selection groups detections by court position. It works within a clip; a player who leaves and re-enters after a long gap may not re-link (appearance-based re-identification is a planned improvement).")
                    .font(.caption2)
                    .foregroundStyle(.tertiary)
                    .padding(.top, 8)
            }
            .padding()
            .animation(.easeInOut, value: viewModel.selectedID)
        }
        .task { await viewModel.loadThumbnails() }
        .navigationTitle("Players")
    }
}

// MARK: - Subviews

private struct PlayerThumbCell: View {
    let candidate: PlayerCandidate
    let image: UIImage?
    let isSelected: Bool

    var body: some View {
        VStack(spacing: 6) {
            ZStack {
                if let image = image {
                    Image(uiImage: image)
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                } else {
                    Rectangle()
                        .fill(.quaternary)
                        .overlay(ProgressView())
                }
            }
            .frame(width: 100, height: 120)
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(isSelected ? Color.accentColor : Color.clear, lineWidth: 3)
            )

            HStack(spacing: 4) {
                Text(candidate.displayName).font(.caption).bold()
                if candidate.isLikelyUser {
                    Image(systemName: "star.fill").font(.caption2).foregroundStyle(.yellow)
                }
            }
            if !candidate.courtLabel.isEmpty {
                Text(courtLabelKey(candidate.courtLabel))
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
        }
    }

    /// Maps the internal "Near Left" style label to a localizable key so SwiftUI
    /// resolves it to French when the app is in French.
    private func courtLabelKey(_ raw: String) -> LocalizedStringKey {
        switch raw {
        case "Near Left": return "Near Left"
        case "Near Right": return "Near Right"
        case "Far Left": return "Far Left"
        case "Far Right": return "Far Right"
        case "Near": return "Near"
        case "Far": return "Far"
        default: return LocalizedStringKey(raw)
        }
    }
}

private struct PlayerStatsPanel: View {
    let candidate: PlayerCandidate
    let stats: PlayerStats

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("\(candidate.displayName) — your stats")
                .font(.headline)

            statRow("Court coverage", String(format: "%.0f%%", stats.coveragePercent))
            statRow("Average depth", depthLabel(stats.averageDepth))
            statRow("Side bias", balanceLabel(stats.leftRightBalance))
            statRow("Tracked frames", "\(stats.detectionCount)")
            statRow("Detection confidence", String(format: "%.0f%%", stats.averageConfidence * 100))
        }
        .padding()
        .background(RoundedRectangle(cornerRadius: 16).fill(.ultraThinMaterial))
    }

    private func statRow(_ label: String, _ value: String) -> some View {
        HStack {
            Text(label).foregroundStyle(.secondary)
            Spacer()
            Text(value).bold().monospacedDigit()
        }
        .font(.subheadline)
    }

    // y grows downward: high = near the camera / net side, low = far / baseline.
    private func depthLabel(_ y: Double) -> String {
        switch y {
        case ..<0.33: return "Back court"
        case ..<0.67: return "Mid court"
        default: return "Front / net"
        }
    }

    private func balanceLabel(_ b: Double) -> String {
        if abs(b) < 0.15 { return "Balanced" }
        return b > 0 ? "Favours right" : "Favours left"
    }
}
