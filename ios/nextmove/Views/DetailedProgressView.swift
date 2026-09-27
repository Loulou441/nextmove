//
//  DetailedProgressView.swift
//  nextmove
//
//  Created by Asmae  on 09/03/2026.
//

import SwiftUI

struct DetailedProgressView: View {
    let recordings: [GameRecording]

    /// Only recordings that have completed analysis results to draw from.
    private var analyzedRecordings: [GameRecording] {
        recordings.filter { $0.status == .completed && $0.analysis != nil }
    }

    private var analyses: [GameAnalysis] {
        analyzedRecordings.compactMap { $0.analysis }
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                if analyses.isEmpty {
                    emptyState
                } else {
                    headerSection
                    summarySection
                    skillsSection
                    aggregateStatsSection
                    ratingTrendSection
                }
            }
            .padding()
        }
        .navigationTitle("Detailed Stats")
        .navigationBarTitleDisplayMode(.inline)
    }

    // MARK: - Empty State

    private var emptyState: some View {
        VStack(spacing: 12) {
            Image(systemName: "chart.bar.xaxis")
                .font(.system(size: 48))
                .foregroundStyle(.secondary)
            Text("No analyzed games yet")
                .font(.headline)
            Text("Record and analyze a game to see your detailed statistics here.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 60)
    }

    // MARK: - Header

    private var headerSection: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Detailed Statistics")
                .font(.title2)
                .fontWeight(.bold)
                .frame(maxWidth: .infinity, alignment: .leading)
            Text("Aggregated across \(analyses.count) analyzed game\(analyses.count == 1 ? "" : "s")")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    // MARK: - Summary Cards

    private var summarySection: some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
            ProgressCard(
                title: "Average Rating",
                value: String(format: "%.1f", averageRating),
                trend: "\(analyses.count) games",
                icon: "star.fill",
                color: .green
            )
            ProgressCard(
                title: "Total Rallies",
                value: "\(totalRallies)",
                trend: "avg \(averageRalliesPerGame)",
                icon: "arrow.left.arrow.right",
                color: .blue
            )
            ProgressCard(
                title: "Winners",
                value: "\(totalWinners)",
                trend: winnersToErrorsRatio,
                icon: "checkmark.circle.fill",
                color: .orange
            )
            ProgressCard(
                title: "Attack Success",
                value: String(format: "%.0f%%", attackSuccessRate),
                trend: "\(totalAttacksSuccessful)/\(totalAttacksAttempted)",
                icon: "bolt.fill",
                color: .purple
            )
        }
    }

    // MARK: - Skills (averaged)

    private var skillsSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Average Skill Ratings")
                .font(.title3)
                .fontWeight(.semibold)

            VStack(spacing: 16) {
                ForEach(averageSkills, id: \.title) { skill in
                    DetailedSkillBar(title: skill.title, rating: skill.rating, icon: skill.icon)
                }
            }
            .padding()
            .background(Color(.systemBackground))
            .clipShape(RoundedRectangle(cornerRadius: 20))
            .shadow(color: .black.opacity(0.06), radius: 12, y: 6)
        }
    }

    // MARK: - Aggregate Stats

    private var aggregateStatsSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Career Totals")
                .font(.title3)
                .fontWeight(.semibold)

            VStack(spacing: 0) {
                StatRow(title: "Games Analyzed", value: "\(analyses.count)", icon: "video.fill")
                Divider().padding(.leading, 44)
                StatRow(title: "Total Rallies", value: "\(totalRallies)", icon: "arrow.left.arrow.right")
                Divider().padding(.leading, 44)
                StatRow(title: "Longest Rally", value: "\(longestRally) shots", icon: "chart.bar.fill")
                Divider().padding(.leading, 44)
                StatRow(title: "Total Winners", value: "\(totalWinners)", icon: "checkmark.circle.fill")
                Divider().padding(.leading, 44)
                StatRow(title: "Total Unforced Errors", value: "\(totalErrors)", icon: "xmark.circle.fill")
                Divider().padding(.leading, 44)
                StatRow(title: "Attacks Attempted", value: "\(totalAttacksAttempted)", icon: "bolt.fill")
                Divider().padding(.leading, 44)
                StatRow(title: "Attacks Successful", value: "\(totalAttacksSuccessful)", icon: "target")
                Divider().padding(.leading, 44)
                StatRow(
                    title: "Attack Success Rate",
                    value: String(format: "%.0f%%", attackSuccessRate),
                    icon: "percent"
                )
                Divider().padding(.leading, 44)
                StatRow(
                    title: "Avg Court Coverage",
                    value: String(format: "%.0f%%", averageCourtCoverage),
                    icon: "figure.walk"
                )
                Divider().padding(.leading, 44)
                StatRow(title: "Total Highlights", value: "\(totalHighlights)", icon: "star.fill")
            }
            .padding()
            .background(Color(.systemBackground))
            .clipShape(RoundedRectangle(cornerRadius: 20))
            .shadow(color: .black.opacity(0.06), radius: 12, y: 6)
        }
    }

    // MARK: - Rating Trend

    private var ratingTrendSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Rating by Game")
                .font(.title3)
                .fontWeight(.semibold)

            VStack(spacing: 12) {
                ForEach(ratingTrend, id: \.id) { entry in
                    HStack(spacing: 12) {
                        Text(entry.title)
                            .font(.subheadline)
                            .lineLimit(1)
                            .frame(maxWidth: .infinity, alignment: .leading)

                        GeometryReader { geo in
                            ZStack(alignment: .leading) {
                                Capsule()
                                    .fill(Color(.systemGray5))
                                Capsule()
                                    .fill(Color.green)
                                    .frame(width: geo.size.width * CGFloat(min(max(entry.rating / 5.0, 0), 1)))
                            }
                        }
                        .frame(width: 100, height: 8)

                        Text(String(format: "%.1f", entry.rating))
                            .font(.subheadline)
                            .fontWeight(.semibold)
                            .foregroundStyle(.secondary)
                            .frame(width: 32, alignment: .trailing)
                    }
                }
            }
            .padding()
            .background(Color(.systemBackground))
            .clipShape(RoundedRectangle(cornerRadius: 20))
            .shadow(color: .black.opacity(0.06), radius: 12, y: 6)
        }
    }

    // MARK: - Aggregation Helpers

    private var averageRating: Double {
        guard !analyses.isEmpty else { return 0 }
        return analyses.map(\.overallRating).reduce(0, +) / Double(analyses.count)
    }

    private var totalRallies: Int { analyses.map(\.statistics.totalRallies).reduce(0, +) }
    private var totalWinners: Int { analyses.map(\.statistics.winners).reduce(0, +) }
    private var totalErrors: Int { analyses.map(\.statistics.errors).reduce(0, +) }
    private var totalAttacksAttempted: Int { analyses.map(\.statistics.attacksAttempted).reduce(0, +) }
    private var totalAttacksSuccessful: Int { analyses.map(\.statistics.attacksSuccessful).reduce(0, +) }
    private var totalHighlights: Int { analyses.map { $0.highlights.count }.reduce(0, +) }
    private var longestRally: Int { analyses.map(\.statistics.longestRally).max() ?? 0 }

    private var averageRalliesPerGame: Int {
        guard !analyses.isEmpty else { return 0 }
        return totalRallies / analyses.count
    }

    private var attackSuccessRate: Double {
        Double(totalAttacksSuccessful) / Double(max(totalAttacksAttempted, 1)) * 100
    }

    private var averageCourtCoverage: Double {
        guard !analyses.isEmpty else { return 0 }
        return analyses.map(\.statistics.courtCoveragePercent).reduce(0, +) / Double(analyses.count)
    }

    private var winnersToErrorsRatio: String {
        guard totalErrors > 0 else { return "\(totalWinners) W" }
        return String(format: "%.1f W/E", Double(totalWinners) / Double(totalErrors))
    }

    private var averageSkills: [(title: String, rating: Double, icon: String)] {
        guard !analyses.isEmpty else { return [] }
        let count = Double(analyses.count)
        func avg(_ keyPath: KeyPath<GameAnalysis.SkillRatings, Double>) -> Double {
            analyses.map { $0.skillRatings[keyPath: keyPath] }.reduce(0, +) / count
        }
        return [
            ("Serve", avg(\.serve), "figure.tennis"),
            ("Return", avg(\.return), "arrow.turn.up.left"),
            ("Third Shot", avg(\.thirdShot), "3.circle.fill"),
            ("Dinking", avg(\.dinking), "hand.tap"),
            ("Volleys", avg(\.volleys), "bolt.fill"),
            ("Movement", avg(\.movement), "figure.walk")
        ]
    }

    private struct RatingEntry: Identifiable {
        let id: UUID
        let title: String
        let rating: Double
    }

    private var ratingTrend: [RatingEntry] {
        analyzedRecordings
            .sorted { $0.date < $1.date }
            .compactMap { recording in
                guard let analysis = recording.analysis else { return nil }
                return RatingEntry(id: recording.id, title: recording.title, rating: analysis.overallRating)
            }
    }
}

// MARK: - Skill Bar

private struct DetailedSkillBar: View {
    let title: String
    let rating: Double
    let icon: String

    // Ratings are on a 0–5 scale (matches GameAnalysis / SkillsSection / MeView).
    private var barColor: Color {
        switch rating {
        case 4...: return .green
        case 3..<4: return .blue
        case 2..<3: return .orange
        default: return .red
        }
    }

    var body: some View {
        VStack(spacing: 6) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.caption)
                    .foregroundStyle(barColor)
                    .frame(width: 20)
                Text(title)
                    .font(.subheadline)
                Spacer()
                Text(String(format: "%.1f", rating))
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundStyle(.secondary)
            }

            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Capsule()
                        .fill(Color(.systemGray5))
                    Capsule()
                        .fill(barColor)
                        .frame(width: geo.size.width * CGFloat(min(max(rating / 5.0, 0), 1)))
                }
            }
            .frame(height: 8)
        }
    }
}
