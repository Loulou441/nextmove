//
//  EvolutionView.swift
//  nextmove
//
//  « Évolution » — miroir iOS de l'écran web /stats. Trace la progression du
//  joueur au fil de ses matchs analysés : la note globale (/5) et la couverture
//  de terrain (%) dans le temps. Source : les enregistrements locaux déjà
//  analysés du sport courant (toujours disponibles, même hors-ligne), triés
//  par date croissante. Il faut au moins 2 matchs pour afficher une évolution.
//

import SwiftUI
import Charts

struct EvolutionView: View {
    let recordings: [GameRecording]

    private let ratingColor = Color.green
    private let coverageColor = Color.blue

    /// Points du graphe : un par match analysé, trié du plus ancien au plus
    /// récent (comme le web).
    private struct Point: Identifiable {
        let id: UUID
        let date: Date
        let title: String
        let rating: Double
        let coverage: Double
    }

    private var points: [Point] {
        recordings
            .filter { $0.status == .completed && $0.analysis != nil }
            .sorted { $0.date < $1.date }
            .compactMap { rec in
                guard let a = rec.analysis else { return nil }
                return Point(
                    id: rec.id,
                    date: rec.date,
                    title: rec.title,
                    rating: a.overallRating,
                    coverage: a.statistics.courtCoveragePercent
                )
            }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                header

                if points.count < 2 {
                    notEnoughState
                } else {
                    heroCard
                    chartCard
                    summaryCards
                }
            }
            .padding()
        }
        .background(
            LinearGradient(
                colors: [ratingColor.opacity(0.06), Color(.systemGroupedBackground)],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()
        )
        .navigationTitle("Évolution")
        .navigationBarTitleDisplayMode(.inline)
    }

    // MARK: - Header

    private var header: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Évolution")
                .font(.largeTitle)
                .fontWeight(.bold)
            Text("Ta progression au fil de tes matchs analysés.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    // MARK: - Hero card (headline progression)

    private var heroCard: some View {
        let first = points.first
        let last = points.last
        let delta = (last?.rating ?? 0) - (first?.rating ?? 0)
        let up = delta >= 0

        return HStack(spacing: 16) {
            ZStack {
                Circle()
                    .fill(ratingColor.opacity(0.15))
                    .frame(width: 58, height: 58)
                Image(systemName: "chart.line.uptrend.xyaxis")
                    .font(.system(size: 24, weight: .semibold))
                    .foregroundStyle(ratingColor)
            }

            VStack(alignment: .leading, spacing: 3) {
                Text("Note actuelle")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Text(String(format: "%.1f", last?.rating ?? 0) + " /5")
                    .font(.system(size: 30, weight: .bold, design: .rounded))
                HStack(spacing: 4) {
                    Image(systemName: up ? "arrow.up.right" : "arrow.down.right")
                    Text(String(format: "%@%.1f depuis ton 1er match", up ? "+" : "", delta))
                }
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundStyle(up ? ratingColor : .red)
            }

            Spacer()
        }
        .padding(18)
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .shadow(color: .black.opacity(0.06), radius: 12, y: 6)
    }

    // MARK: - Chart

    private var chartCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Note et couverture de terrain")
                    .font(.subheadline)
                    .fontWeight(.semibold)
                Spacer()
            }

            Chart {
                ForEach(points) { p in
                    // Note (/5) — ramenée sur 0–100 pour partager l'axe avec la
                    // couverture ; la légende précise l'échelle réelle.
                    let scaledRating = p.rating / 5.0 * 100

                    AreaMark(
                        x: .value("Date", p.date),
                        y: .value("Valeur", scaledRating),
                        series: .value("Série", "Note (/5)")
                    )
                    .foregroundStyle(
                        LinearGradient(
                            colors: [ratingColor.opacity(0.28), ratingColor.opacity(0.02)],
                            startPoint: .top, endPoint: .bottom
                        )
                    )
                    .interpolationMethod(.catmullRom)

                    LineMark(
                        x: .value("Date", p.date),
                        y: .value("Valeur", scaledRating),
                        series: .value("Série", "Note (/5)")
                    )
                    .foregroundStyle(ratingColor)
                    .lineStyle(StrokeStyle(lineWidth: 3, lineCap: .round))
                    .interpolationMethod(.catmullRom)
                    .symbol {
                        Circle()
                            .fill(ratingColor)
                            .frame(width: 8, height: 8)
                            .shadow(color: ratingColor.opacity(0.4), radius: 2)
                    }

                    LineMark(
                        x: .value("Date", p.date),
                        y: .value("Valeur", p.coverage),
                        series: .value("Série", "Couverture (%)")
                    )
                    .foregroundStyle(coverageColor)
                    .lineStyle(StrokeStyle(lineWidth: 2.5, lineCap: .round, dash: [5, 4]))
                    .interpolationMethod(.catmullRom)
                    .symbol {
                        Circle()
                            .fill(coverageColor)
                            .frame(width: 7, height: 7)
                    }
                }
            }
            .chartYScale(domain: 0...100)
            .chartYAxis {
                AxisMarks(position: .leading, values: [0, 25, 50, 75, 100]) {
                    AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5, dash: [3, 3]))
                        .foregroundStyle(Color(.separator).opacity(0.6))
                    AxisValueLabel()
                }
            }
            .chartXAxis {
                AxisMarks(values: .automatic(desiredCount: min(points.count, 5))) { _ in
                    AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5, dash: [3, 3]))
                        .foregroundStyle(Color(.separator).opacity(0.4))
                    AxisValueLabel(format: .dateTime.day().month(.twoDigits))
                }
            }
            .frame(height: 240)

            HStack(spacing: 18) {
                legendItem(color: ratingColor, label: "Note (/5)", dashed: false)
                legendItem(color: coverageColor, label: "Couverture (%)", dashed: true)
            }
            .font(.caption)
            .foregroundStyle(.secondary)
        }
        .padding(18)
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .shadow(color: .black.opacity(0.06), radius: 12, y: 6)
    }

    private func legendItem(color: Color, label: String, dashed: Bool) -> some View {
        HStack(spacing: 6) {
            RoundedRectangle(cornerRadius: 1)
                .fill(color)
                .frame(width: 16, height: 3)
                .opacity(dashed ? 0.6 : 1)
            Text(label)
        }
    }

    // MARK: - Summary cards (première vs dernière analyse)

    private var summaryCards: some View {
        let first = points.first
        let last = points.last
        let ratingDelta = (last?.rating ?? 0) - (first?.rating ?? 0)
        let coverageDelta = (last?.coverage ?? 0) - (first?.coverage ?? 0)

        return LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
            deltaCard(
                title: "Note",
                icon: "star.fill",
                current: String(format: "%.1f", last?.rating ?? 0),
                delta: ratingDelta,
                unit: "",
                color: ratingColor
            )
            deltaCard(
                title: "Couverture",
                icon: "figure.walk",
                current: String(format: "%.0f%%", last?.coverage ?? 0),
                delta: coverageDelta,
                unit: "%",
                color: coverageColor
            )
        }
    }

    private func deltaCard(title: String, icon: String, current: String, delta: Double, unit: String, color: Color) -> some View {
        let up = delta >= 0
        return VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.caption)
                    .foregroundStyle(color)
                    .frame(width: 26, height: 26)
                    .background(color.opacity(0.15))
                    .clipShape(Circle())
                Text(title)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Spacer()
            }
            Text(current)
                .font(.system(size: 26, weight: .bold, design: .rounded))
            HStack(spacing: 4) {
                Image(systemName: up ? "arrow.up.right" : "arrow.down.right")
                Text(String(format: "%@%.1f%@", up ? "+" : "", delta, unit))
            }
            .font(.caption)
            .fontWeight(.semibold)
            .foregroundStyle(up ? ratingColor : .red)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .shadow(color: .black.opacity(0.05), radius: 8, y: 4)
    }

    // MARK: - Empty state

    private var notEnoughState: some View {
        VStack(spacing: 14) {
            ZStack {
                Circle()
                    .fill(ratingColor.opacity(0.12))
                    .frame(width: 76, height: 76)
                Image(systemName: "chart.line.uptrend.xyaxis")
                    .font(.system(size: 34, weight: .semibold))
                    .foregroundStyle(ratingColor)
            }
            Text("Pas encore assez de données")
                .font(.headline)
            Text("Analyse au moins 2 matchs pour voir ta progression se dessiner ici.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 48)
        .padding(.horizontal, 24)
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .shadow(color: .black.opacity(0.05), radius: 10, y: 5)
    }
}

#Preview {
    NavigationStack {
        EvolutionView(recordings: [])
    }
}
