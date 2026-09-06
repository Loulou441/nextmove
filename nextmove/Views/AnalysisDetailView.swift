//
//  AnalysisDetailView.swift
//  nextmove
//

import SwiftUI
import AVKit
import Combine

struct AnalysisDetailView: View {
    /// The recording passed in at navigation time. Used only to identify which
    /// recording to display; live state is read from the view model below.
    let recording: GameRecording
    @ObservedObject var viewModel: RecordingViewModel
    @State private var selectedTab = 0
    @StateObject private var playerManager = VideoPlayerManager()
    @Environment(\.dismiss) private var dismiss

    /// Always reflects the latest state of this recording from the view model,
    /// so status/analysis updates (pending → processing → completed) redraw the UI.
    private var liveRecording: GameRecording {
        viewModel.recordings.first(where: { $0.id == recording.id }) ?? recording
    }

    var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                VStack(spacing: 0) {
                    if liveRecording.status == .completed, let analysis = liveRecording.analysis {
                        videoPlayerSection
                            .id("videoPlayer")

                        askCoachButton(analysis: analysis)

                        tabSelector

                        Group {
                            switch selectedTab {
                            case 0:
                                OverviewSection(analysis: analysis)
                            case 1:
                                SkillsSection(skillRatings: analysis.skillRatings)
                            case 2:
                                HighlightsSection(highlights: analysis.highlights) { timestamp in
                                    // Seek the video to the highlight and scroll up to the player.
                                    playerManager.seek(toSeconds: timestamp)
                                    withAnimation {
                                        proxy.scrollTo("videoPlayer", anchor: .top)
                                    }
                                }
                            case 3:
                                StatisticsSection(statistics: analysis.statistics)
                            default:
                                EmptyView()
                            }
                        }
                        .padding()
                    } else {
                        processingView
                    }
                }
            }
        }
        .background(Color(.systemGroupedBackground))
        .navigationTitle(recording.title)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Menu {
                    Button {
                        // Share action
                    } label: {
                        Label("Share Analysis", systemImage: "square.and.arrow.up")
                    }
                    
                    Button {
                        // Export action
                    } label: {
                        Label("Export Video", systemImage: "arrow.down.doc")
                    }
                } label: {
                    Image(systemName: "ellipsis.circle")
                }
            }
        }
    }

    /// Entry point into the conversational AI coach, grounded in this game's analysis.
    private func askCoachButton(analysis: GameAnalysis) -> some View {
        NavigationLink {
            CoachChatView(sportType: recording.sportType, analysis: analysis)
        } label: {
            HStack(spacing: 12) {
                Image(systemName: "bubble.left.and.text.bubble.right.fill")
                    .font(.title3)
                VStack(alignment: .leading, spacing: 2) {
                    Text("Ask your AI Coach")
                        .font(.subheadline)
                        .fontWeight(.semibold)
                    Text("Get personalized tips based on this game")
                        .font(.caption)
                        .foregroundStyle(.white.opacity(0.85))
                }
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.caption)
            }
            .foregroundStyle(.white)
            .padding()
            .background(
                LinearGradient(
                    colors: [recording.sportType.color, recording.sportType.color.opacity(0.75)],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .clipShape(RoundedRectangle(cornerRadius: 16))
            .padding()
        }
        .buttonStyle(.plain)
    }
    
    private var videoPlayerSection: some View {
        ZStack {
            if let videoURL = recording.videoURL {
                GeometryReader { geometry in
                    ZStack {
                        if let player = playerManager.player {
                            VideoPlayer(player: player)
                                .frame(width: geometry.size.width, height: geometry.size.width * 9/16)
                                .background(Color.black)
                                .onAppear {
                                    // Ensure player is ready
                                    player.currentItem?.preferredForwardBufferDuration = 1.0
                                }
                        } else {
                            Color.black
                                .frame(width: geometry.size.width, height: geometry.size.width * 9/16)
                                .overlay {
                                    ProgressView()
                                        .tint(.white)
                                }
                        }
                        
                        // Play button overlay
                        if !playerManager.isPlaying {
                            Button {
                                playerManager.play()
                            } label: {
                                ZStack {
                                    Circle()
                                        .fill(Color.black.opacity(0.6))
                                        .frame(width: 80, height: 80)
                                    
                                    Image(systemName: "play.fill")
                                        .font(.system(size: 40))
                                        .foregroundStyle(.white)
                                }
                            }
                        }
                    }
                }
                .aspectRatio(16/9, contentMode: .fit)
                .onAppear {
                    playerManager.setupPlayer(url: videoURL)
                }
                .onDisappear {
                    playerManager.pause()
                }
            } else {
                Rectangle()
                    .fill(Color.black)
                    .aspectRatio(16/9, contentMode: .fit)
                    .overlay {
                        VStack(spacing: 12) {
                            Image(systemName: "video.slash")
                                .font(.system(size: 60))
                                .foregroundStyle(.white.opacity(0.5))
                            
                            Text("Video not available")
                                .font(.caption)
                                .foregroundStyle(.white.opacity(0.7))
                        }
                    }
            }
        }
        .overlay(alignment: .bottomLeading) {
            Text(formatDuration(recording.duration))
                .font(.caption)
                .fontWeight(.medium)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(.ultraThinMaterial)
                .clipShape(RoundedRectangle(cornerRadius: 6))
                .padding(12)
        }
    }
    
    private var tabSelector: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                TabButton(title: "Overview", isSelected: selectedTab == 0) {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        selectedTab = 0
                    }
                }
                TabButton(title: "Skills", isSelected: selectedTab == 1) {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        selectedTab = 1
                    }
                }
                TabButton(title: "Highlights", isSelected: selectedTab == 2) {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        selectedTab = 2
                    }
                }
                TabButton(title: "Stats", isSelected: selectedTab == 3) {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        selectedTab = 3
                    }
                }
            }
            .padding(.horizontal)
        }
        .padding(.vertical, 16)
        .background(Color(.systemBackground))
    }
    
    private var processingView: some View {
        VStack(spacing: 24) {
            Spacer()

            ZStack {
                Circle()
                    .stroke(Color.blue.opacity(0.2), lineWidth: 8)
                    .frame(width: 100, height: 100)

                if liveRecording.status == .processing {
                    ProgressView()
                        .scaleEffect(1.5)
                } else {
                    Image(systemName: liveRecording.status == .failed ? "exclamationmark.triangle" : "wand.and.stars")
                        .font(.system(size: 36))
                        .foregroundStyle(liveRecording.status == .failed ? .orange : .blue)
                }
            }

            VStack(spacing: 8) {
                Text(statusTitle)
                    .font(.title3)
                    .fontWeight(.semibold)

                if liveRecording.status == .processing {
                    // Live progress from the pipeline
                    Text(viewModel.analysisProgress.isEmpty ? "Processing your video..." : viewModel.analysisProgress)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)

                    ProgressView(value: viewModel.analysisProgressPercentage)
                        .tint(.blue)
                        .padding(.horizontal, 40)
                } else if liveRecording.status == .failed {
                    Text(viewModel.analysisError ?? "Analysis failed. Please try again.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                } else {
                    Text("Tap below to analyze this game and get your stats and coaching.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                }
            }

            // Start / retry button when not already processing
            if liveRecording.status != .processing {
                Button {
                    let rec = liveRecording
                    Task.detached(priority: .userInitiated) { [weak viewModel] in
                        await viewModel?.processRecording(rec)
                    }
                } label: {
                    HStack {
                        Image(systemName: "wand.and.stars")
                        Text(liveRecording.status == .failed ? "Retry Analysis" : "Analyze Game")
                    }
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .padding(.horizontal, 28)
                    .padding(.vertical, 12)
                    .background(Color.blue)
                    .foregroundStyle(.white)
                    .clipShape(Capsule())
                }
            }

            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding()
    }

    private var statusTitle: String {
        switch liveRecording.status {
        case .processing: return "Analyzing your game..."
        case .failed:      return "Analysis didn't finish"
        default:           return "Ready to analyze"
        }
    }
    
    private func formatDuration(_ duration: TimeInterval) -> String {
        let minutes = Int(duration) / 60
        let seconds = Int(duration) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}

struct TabButton: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.subheadline)
                .fontWeight(isSelected ? .semibold : .regular)
                .foregroundStyle(isSelected ? .white : .primary)
                .padding(.horizontal, 20)
                .padding(.vertical, 10)
                .background(
                    isSelected ?
                    AnyView(LinearGradient(colors: [.blue, .blue.opacity(0.8)], startPoint: .leading, endPoint: .trailing)) :
                    AnyView(Color(.secondarySystemBackground))
                )
                .clipShape(Capsule())
        }
    }
}

struct OverviewSection: View {
    let analysis: GameAnalysis
    
    var body: some View {
        VStack(spacing: 20) {
            overallRatingCard
            insightsCard
            quickStatsGrid
        }
    }
    
    private var overallRatingCard: some View {
        VStack(spacing: 16) {
            Text("Overall Performance")
                .font(.title3)
                .fontWeight(.semibold)
            
            ZStack {
                Circle()
                    .stroke(Color.gray.opacity(0.15), lineWidth: 20)
                    .frame(width: 140, height: 140)
                
                Circle()
                    .trim(from: 0, to: analysis.overallRating / 5.0)
                    .stroke(
                        LinearGradient(
                            colors: [ratingColor(analysis.overallRating), ratingColor(analysis.overallRating).opacity(0.7)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        style: StrokeStyle(lineWidth: 20, lineCap: .round)
                    )
                    .frame(width: 140, height: 140)
                    .rotationEffect(.degrees(-90))
                    .animation(.easeInOut(duration: 1.0), value: analysis.overallRating)
                
                VStack(spacing: 4) {
                    Text(String(format: "%.1f", analysis.overallRating))
                        .font(.system(size: 44, weight: .bold, design: .rounded))
                    Text("/ 5.0")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            
            HStack(spacing: 8) {
                Image(systemName: ratingIcon(analysis.overallRating))
                    .foregroundStyle(ratingColor(analysis.overallRating))
                Text(ratingDescription(analysis.overallRating))
                    .font(.subheadline)
                    .fontWeight(.medium)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
            .background(ratingColor(analysis.overallRating).opacity(0.1))
            .clipShape(Capsule())
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 24)
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .shadow(color: .black.opacity(0.06), radius: 12, y: 6)
    }
    
    private var insightsCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Key Insights", systemImage: "lightbulb.fill")
                .font(.headline)
                .foregroundStyle(.orange)
            
            VStack(alignment: .leading, spacing: 8) {
                InsightRow(
                    icon: "arrow.up.circle.fill",
                    text: "Strong serve performance",
                    color: .green
                )
                InsightRow(
                    icon: "target",
                    text: "Focus on third shot consistency",
                    color: .orange
                )
                InsightRow(
                    icon: "figure.walk",
                    text: "Excellent court coverage",
                    color: .blue
                )
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .shadow(color: .black.opacity(0.05), radius: 8, y: 4)
    }
    
    private var quickStatsGrid: some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
            QuickStatCard(title: "Rallies", value: "\(analysis.statistics.totalRallies)", icon: "arrow.left.arrow.right", color: .blue)
            QuickStatCard(title: "Winners", value: "\(analysis.statistics.winners)", icon: "checkmark.circle.fill", color: .green)
            QuickStatCard(title: "Errors", value: "\(analysis.statistics.errors)", icon: "xmark.circle.fill", color: .red)
            QuickStatCard(title: "Coverage", value: "\(Int(analysis.statistics.courtCoveragePercent))%", icon: "figure.walk", color: .orange)
        }
    }
    
    private func ratingColor(_ rating: Double) -> Color {
        switch rating {
        case 4.5...: return .green
        case 3.5..<4.5: return .blue
        case 2.5..<3.5: return .orange
        default: return .red
        }
    }
    
    private func ratingIcon(_ rating: Double) -> String {
        switch rating {
        case 4.5...: return "star.fill"
        case 3.5..<4.5: return "hand.thumbsup.fill"
        case 2.5..<3.5: return "chart.line.uptrend.xyaxis"
        default: return "arrow.up.circle"
        }
    }
    
    private func ratingDescription(_ rating: Double) -> String {
        switch rating {
        case 4.5...: return "Excellent Performance"
        case 3.5..<4.5: return "Strong Performance"
        case 2.5..<3.5: return "Good Performance"
        default: return "Room for Improvement"
        }
    }
}

struct InsightRow: View {
    let icon: String
    let text: String
    let color: Color
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.caption)
                .foregroundStyle(color)
                .frame(width: 20)
            
            Text(text)
                .font(.subheadline)
                .foregroundStyle(.primary)
            
            Spacer()
        }
    }
}

struct QuickStatCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(color.opacity(0.15))
                    .frame(width: 50, height: 50)
                
                Image(systemName: icon)
                    .font(.title3)
                    .foregroundStyle(color)
            }
            
            Text(value)
                .font(.title2)
                .fontWeight(.bold)
                .foregroundStyle(.primary)
            
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 20)
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .shadow(color: .black.opacity(0.05), radius: 8, y: 4)
    }
}

struct SkillsSection: View {
    let skillRatings: GameAnalysis.SkillRatings
    
    var body: some View {
        VStack(spacing: 20) {
            headerSection
            skillBarsSection
            strengthsWeaknessesSection
        }
    }
    
    private var headerSection: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Skill Breakdown")
                    .font(.title3)
                    .fontWeight(.semibold)
                Text("Detailed performance by category")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
        }
    }
    
    private var skillBarsSection: some View {
        VStack(spacing: 16) {
            SkillBar(title: "Serve", rating: skillRatings.serve, icon: "figure.tennis")
            SkillBar(title: "Return", rating: skillRatings.return, icon: "arrow.turn.up.left")
            SkillBar(title: "Third Shot", rating: skillRatings.thirdShot, icon: "3.circle.fill")
            SkillBar(title: "Dinking", rating: skillRatings.dinking, icon: "hand.tap")
            SkillBar(title: "Volleys", rating: skillRatings.volleys, icon: "bolt.fill")
            SkillBar(title: "Movement", rating: skillRatings.movement, icon: "figure.walk")
        }
        .padding()
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .shadow(color: .black.opacity(0.06), radius: 12, y: 6)
    }
    
    private var strengthsWeaknessesSection: some View {
        HStack(spacing: 12) {
            strengthsCard
            weaknessesCard
        }
    }
    
    private var strengthsCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Strengths", systemImage: "star.fill")
                .font(.subheadline)
                .fontWeight(.semibold)
                .foregroundStyle(.green)
            
            VStack(alignment: .leading, spacing: 6) {
                ForEach(topSkills(), id: \.0) { skill, rating in
                    HStack {
                        Text(skill)
                            .font(.caption)
                        Spacer()
                        Text(String(format: "%.1f", rating))
                            .font(.caption)
                            .fontWeight(.semibold)
                            .foregroundStyle(.green)
                    }
                }
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.green.opacity(0.08))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
    
    private var weaknessesCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Focus Areas", systemImage: "target")
                .font(.subheadline)
                .fontWeight(.semibold)
                .foregroundStyle(.orange)
            
            VStack(alignment: .leading, spacing: 6) {
                ForEach(bottomSkills(), id: \.0) { skill, rating in
                    HStack {
                        Text(skill)
                            .font(.caption)
                        Spacer()
                        Text(String(format: "%.1f", rating))
                            .font(.caption)
                            .fontWeight(.semibold)
                            .foregroundStyle(.orange)
                    }
                }
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.orange.opacity(0.08))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
    
    private func topSkills() -> [(String, Double)] {
        let skills = [
            ("Serve", skillRatings.serve),
            ("Return", skillRatings.return),
            ("Third Shot", skillRatings.thirdShot),
            ("Dinking", skillRatings.dinking),
            ("Volleys", skillRatings.volleys),
            ("Movement", skillRatings.movement)
        ]
        return skills.sorted { $0.1 > $1.1 }.prefix(2).map { ($0.0, $0.1) }
    }
    
    private func bottomSkills() -> [(String, Double)] {
        let skills = [
            ("Serve", skillRatings.serve),
            ("Return", skillRatings.return),
            ("Third Shot", skillRatings.thirdShot),
            ("Dinking", skillRatings.dinking),
            ("Volleys", skillRatings.volleys),
            ("Movement", skillRatings.movement)
        ]
        return skills.sorted { $0.1 < $1.1 }.prefix(2).map { ($0.0, $0.1) }
    }
}

struct SkillBar: View {
    let title: String
    let rating: Double
    let icon: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                HStack(spacing: 8) {
                    Image(systemName: icon)
                        .font(.caption)
                        .foregroundStyle(skillColor(rating))
                        .frame(width: 20)
                    
                    Text(title)
                        .font(.subheadline)
                        .fontWeight(.medium)
                }
                
                Spacer()
                
                Text(String(format: "%.1f", rating))
                    .font(.subheadline)
                    .fontWeight(.bold)
                    .foregroundStyle(skillColor(rating))
            }
            
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 6)
                        .fill(Color.gray.opacity(0.15))
                    
                    RoundedRectangle(cornerRadius: 6)
                        .fill(
                            LinearGradient(
                                colors: [skillColor(rating), skillColor(rating).opacity(0.7)],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .frame(width: geometry.size.width * (rating / 5.0))
                        .animation(.easeInOut(duration: 0.8), value: rating)
                }
            }
            .frame(height: 10)
        }
    }
    
    private func skillColor(_ rating: Double) -> Color {
        switch rating {
        case 4.0...: return .green
        case 3.0..<4.0: return .blue
        case 2.0..<3.0: return .orange
        default: return .red
        }
    }
}

struct HighlightsSection: View {
    let highlights: [GameAnalysis.Highlight]
    /// Called with the highlight's timestamp (seconds) when a card is tapped.
    var onSelect: ((TimeInterval) -> Void)? = nil

    var body: some View {
        VStack(spacing: 20) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Game Highlights")
                        .font(.title3)
                        .fontWeight(.semibold)
                    Text("\(highlights.count) key moments identified")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
            }

            if highlights.isEmpty {
                Text("No highlights detected for this game.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 24)
            }

            VStack(spacing: 12) {
                ForEach(highlights) { highlight in
                    HighlightCard(highlight: highlight, onSelect: onSelect)
                }
            }
        }
    }
}

struct HighlightCard: View {
    let highlight: GameAnalysis.Highlight
    var onSelect: ((TimeInterval) -> Void)? = nil

    var body: some View {
        Button {
            onSelect?(highlight.timestamp)
        } label: {
            HStack(spacing: 16) {
                ZStack {
                    Circle()
                        .fill(highlightColor.opacity(0.15))
                        .frame(width: 50, height: 50)
                    
                    Image(systemName: highlightIcon)
                        .font(.title3)
                        .foregroundStyle(highlightColor)
                }
                
                VStack(alignment: .leading, spacing: 6) {
                    Text(highlight.description)
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundStyle(.primary)
                    
                    HStack(spacing: 8) {
                        Text(formatTimestamp(highlight.timestamp))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        
                        Text("•")
                            .foregroundStyle(.secondary)
                        
                        Text(highlight.type.rawValue.capitalized)
                            .font(.caption)
                            .foregroundStyle(highlightColor)
                    }
                }
                
                Spacer()
                
                Image(systemName: "play.circle.fill")
                    .font(.title2)
                    .foregroundStyle(.blue)
            }
            .padding()
            .background(Color(.systemBackground))
            .clipShape(RoundedRectangle(cornerRadius: 16))
            .shadow(color: .black.opacity(0.05), radius: 8, y: 4)
        }
        .buttonStyle(.plain)
    }
    
    private var highlightIcon: String {
        switch highlight.type {
        case .winner: return "star.fill"
        case .longRally: return "arrow.left.arrow.right.circle.fill"
        case .attack: return "bolt.circle.fill"
        case .greatDefense: return "shield.fill"
        case .error: return "exclamationmark.triangle.fill"
        }
    }
    
    private var highlightColor: Color {
        switch highlight.type {
        case .winner: return .yellow
        case .longRally: return .blue
        case .attack: return .orange
        case .greatDefense: return .green
        case .error: return .red
        }
    }
    
    private func formatTimestamp(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}

struct StatisticsSection: View {
    let statistics: GameAnalysis.GameStatistics
    
    var body: some View {
        VStack(spacing: 20) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Detailed Statistics")
                        .font(.title3)
                        .fontWeight(.semibold)
                    Text("Complete game breakdown")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
            }
            
            VStack(spacing: 0) {
                StatRow(title: "Total Rallies", value: "\(statistics.totalRallies)", icon: "arrow.left.arrow.right")
                Divider().padding(.leading, 44)
                StatRow(title: "Longest Rally", value: "\(statistics.longestRally) shots", icon: "chart.bar.fill")
                Divider().padding(.leading, 44)
                StatRow(title: "Winners", value: "\(statistics.winners)", icon: "checkmark.circle.fill")
                Divider().padding(.leading, 44)
                StatRow(title: "Unforced Errors", value: "\(statistics.errors)", icon: "xmark.circle.fill")
                Divider().padding(.leading, 44)
                StatRow(title: "Attacks Attempted", value: "\(statistics.attacksAttempted)", icon: "bolt.fill")
                Divider().padding(.leading, 44)
                StatRow(title: "Attacks Successful", value: "\(statistics.attacksSuccessful)", icon: "target")
                Divider().padding(.leading, 44)
                StatRow(
                    title: "Attack Success Rate",
                    value: String(format: "%.0f%%", Double(statistics.attacksSuccessful) / Double(max(statistics.attacksAttempted, 1)) * 100),
                    icon: "percent"
                )
                Divider().padding(.leading, 44)
                StatRow(title: "Court Coverage", value: String(format: "%.0f%%", statistics.courtCoveragePercent), icon: "figure.walk")
            }
            .padding()
            .background(Color(.systemBackground))
            .clipShape(RoundedRectangle(cornerRadius: 20))
            .shadow(color: .black.opacity(0.06), radius: 12, y: 6)
        }
    }
}

struct StatRow: View {
    let title: String
    let value: String
    let icon: String
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.caption)
                .foregroundStyle(.blue)
                .frame(width: 20)
            
            Text(title)
                .font(.subheadline)
                .foregroundStyle(.primary)
            
            Spacer()
            
            Text(value)
                .font(.subheadline)
                .fontWeight(.semibold)
                .foregroundStyle(.secondary)
        }
        .padding(.vertical, 12)
    }
}




// MARK: - Video Player Manager

class VideoPlayerManager: ObservableObject {
    @Published var player: AVPlayer?
    @Published var isPlaying = false
    private var timeObserver: Any?
    
    func setupPlayer(url: URL) {
        // Always recreate player to ensure fresh state
        cleanup()
        
        let playerItem = AVPlayerItem(url: url)
        player = AVPlayer(playerItem: playerItem)
        
        // Preload the video
        player?.currentItem?.preferredForwardBufferDuration = 1.0
        
        // Observe playback end
        NotificationCenter.default.addObserver(
            forName: .AVPlayerItemDidPlayToEndTime,
            object: player?.currentItem,
            queue: .main
        ) { [weak self] _ in
            self?.isPlaying = false
            self?.player?.seek(to: .zero)
        }
        
        // Observe playback status
        timeObserver = player?.addPeriodicTimeObserver(
            forInterval: CMTime(seconds: 0.5, preferredTimescale: 600),
            queue: .main
        ) { [weak self] _ in
            guard let self = self, let player = self.player else { return }
            
            // Update playing state based on actual playback rate
            if player.rate > 0 {
                self.isPlaying = true
            } else {
                self.isPlaying = false
            }
        }
    }
    
    func play() {
        player?.play()
        isPlaying = true
    }
    
    func pause() {
        player?.pause()
        isPlaying = false
    }

    /// Seeks the player to the given time (in seconds) and starts playback.
    func seek(toSeconds seconds: Double) {
        guard let player else { return }
        let target = CMTime(seconds: max(0, seconds), preferredTimescale: 600)
        player.seek(to: target, toleranceBefore: .zero, toleranceAfter: .zero) { [weak self] _ in
            player.play()
            self?.isPlaying = true
        }
    }
    
    private func cleanup() {
        if let observer = timeObserver {
            player?.removeTimeObserver(observer)
            timeObserver = nil
        }
        player?.pause()
        player = nil
        NotificationCenter.default.removeObserver(self)
    }
    
    deinit {
        cleanup()
    }
}
