//
//  MatchComparisonView.swift
//  nextmove
//
//  Compare deux matchs analysés côte à côte : note globale, compétences et
//  statistiques clés, avec un indicateur de progression (quel match est
//  meilleur sur chaque métrique). Ne propose que des matchs du MÊME sport et
//  déjà analysés (status == .completed && analysis != nil), pour rester
//  cohérent avec le reste de l'app.
//

import SwiftUI

struct MatchComparisonView: View {
    /// Bassin de matchs comparables (déjà filtré par sport + analysés).
    let recordings: [GameRecording]

    @Environment(\.dismiss) private var dismiss

    @State private var leftID: UUID?
    @State private var rightID: UUID?

    // Résout les enregistrements sélectionnés depuis leur id.
    private var left: GameRecording? { recordings.first { $0.id == leftID } }
    private var right: GameRecording? { recordings.first { $0.id == rightID } }

    var body: some View {
        NavigationStack {
            Group {
                if recordings.count < 2 {
                    notEnoughState
                } else {
                    ScrollView {
                        VStack(spacing: 20) {
                            pickers

                            if let l = left, let r = right,
                               let la = l.analysis, let ra = r.analysis {
                                comparison(l, la, r, ra)
                            } else {
                                Text("Choisis deux matchs à comparer.")
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                                    .padding(.top, 40)
                            }
                        }
                        .padding()
                    }
                }
            }
            .navigationTitle("Comparer")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Fermer") { dismiss() }
                }
            }
            .onAppear(perform: preselect)
        }
    }

    /// Pré-sélectionne les deux matchs les plus récents (la liste est déjà
    /// triée du plus récent au plus ancien par le view model).
    private func preselect() {
        guard leftID == nil, rightID == nil, recordings.count >= 2 else { return }
        leftID = recordings[0].id
        rightID = recordings[1].id
    }

    // MARK: - Pickers

    private var pickers: some View {
        HStack(spacing: 12) {
            matchPicker(title: "Match A", selection: $leftID, exclude: rightID)
            matchPicker(title: "Match B", selection: $rightID, exclude: leftID)
        }
    }

    private func matchPicker(title: String, selection: Binding<UUID?>, exclude: UUID?) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)

            Menu {
                ForEach(recordings) { rec in
                    Button {
                        selection.wrappedValue = rec.id
                    } label: {
                        // Empêche de choisir deux fois le même match.
                        if rec.id == exclude {
                            Label(rec.title, systemImage: "nosign")
                        } else if rec.id == selection.wrappedValue {
                            Label(rec.title, systemImage: "checkmark")
                        } else {
                            Text(rec.title)
                        }
                    }
                    .disabled(rec.id == exclude)
                }
            } label: {
                HStack {
                    Text(recordings.first { $0.id == selection.wrappedValue }?.title ?? "Choisir…")
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .lineLimit(1)
                    Spacer()
                    Image(systemName: "chevron.up.chevron.down")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 10)
                .background(Color(.secondarySystemBackground))
                .clipShape(RoundedRectangle(cornerRadius: 10))
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    // MARK: - Comparison content

    @ViewBuilder
    private func comparison(_ l: GameRecording, _ la: GameAnalysis,
                            _ r: GameRecording, _ ra: GameAnalysis) -> some View {
        // En-tête : dates des deux matchs pour situer la comparaison.
        HStack {
            Text(l.date, style: .date)
            Spacer()
            Text(r.date, style: .date)
        }
        .font(.caption2)
        .foregroundStyle(.secondary)

        overallCard(la.overallRating, ra.overallRating)

        section("Compétences") {
            CompareRow(label: "Service", left: la.skillRatings.serve, right: ra.skillRatings.serve, format: .rating)
            CompareRow(label: "Retour", left: la.skillRatings.`return`, right: ra.skillRatings.`return`, format: .rating)
            CompareRow(label: "3e frappe", left: la.skillRatings.thirdShot, right: ra.skillRatings.thirdShot, format: .rating)
            CompareRow(label: "Dinking", left: la.skillRatings.dinking, right: ra.skillRatings.dinking, format: .rating)
            CompareRow(label: "Volées", left: la.skillRatings.volleys, right: ra.skillRatings.volleys, format: .rating)
            CompareRow(label: "Déplacement", left: la.skillRatings.movement, right: ra.skillRatings.movement, format: .rating)
        }

        section("Statistiques") {
            CompareRow(label: "Échanges", left: Double(la.statistics.totalRallies), right: Double(ra.statistics.totalRallies), format: .count)
            CompareRow(label: "Plus long échange", left: Double(la.statistics.longestRally), right: Double(ra.statistics.longestRally), format: .count)
            CompareRow(label: "Coups gagnants", left: Double(la.statistics.winners), right: Double(ra.statistics.winners), format: .count)
            // Pour les fautes, moins c'est mieux.
            CompareRow(label: "Fautes", left: Double(la.statistics.errors), right: Double(ra.statistics.errors), format: .count, lowerIsBetter: true)
            CompareRow(label: "Réussite attaques", left: attackRate(la.statistics), right: attackRate(ra.statistics), format: .percent)
            CompareRow(label: "Couverture du court", left: la.statistics.courtCoveragePercent, right: ra.statistics.courtCoveragePercent, format: .percent)
        }
    }

    private func attackRate(_ s: GameAnalysis.GameStatistics) -> Double {
        Double(s.attacksSuccessful) / Double(max(s.attacksAttempted, 1)) * 100
    }

    // MARK: - Overall rating card

    private func overallCard(_ leftValue: Double, _ rightValue: Double) -> some View {
        HStack(spacing: 0) {
            overallGauge(leftValue)
            Divider().frame(height: 120)
            overallGauge(rightValue)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 20)
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .shadow(color: .black.opacity(0.06), radius: 12, y: 6)
    }

    private func overallGauge(_ value: Double) -> some View {
        VStack(spacing: 8) {
            Text("Note globale")
                .font(.caption)
                .foregroundStyle(.secondary)
            ZStack {
                Circle()
                    .stroke(Color.gray.opacity(0.15), lineWidth: 12)
                    .frame(width: 90, height: 90)
                Circle()
                    .trim(from: 0, to: value / 5.0)
                    .stroke(ratingColor(value),
                            style: StrokeStyle(lineWidth: 12, lineCap: .round))
                    .frame(width: 90, height: 90)
                    .rotationEffect(.degrees(-90))
                VStack(spacing: 0) {
                    Text(String(format: "%.1f", value))
                        .font(.system(size: 24, weight: .bold, design: .rounded))
                    Text("/ 5.0")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .frame(maxWidth: .infinity)
    }

    private func ratingColor(_ rating: Double) -> Color {
        switch rating {
        case 4.5...: return .green
        case 3.5..<4.5: return .blue
        case 2.5..<3.5: return .orange
        default: return .red
        }
    }

    // MARK: - Section wrapper

    private func section<Content: View>(_ title: LocalizedStringKey,
                                        @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.headline)
            VStack(spacing: 10) {
                content()
            }
            .padding()
            .background(Color(.systemBackground))
            .clipShape(RoundedRectangle(cornerRadius: 16))
            .shadow(color: .black.opacity(0.05), radius: 8, y: 4)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    // MARK: - Empty state

    private var notEnoughState: some View {
        VStack(spacing: 12) {
            Image(systemName: "square.on.square.dashed")
                .font(.system(size: 48))
                .foregroundStyle(.secondary)
            Text("Pas assez de matchs")
                .font(.title3)
                .fontWeight(.semibold)
            Text("Analyse au moins deux matchs de ce sport pour pouvoir les comparer.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)
        }
    }
}

// MARK: - Compare row

/// Une ligne de comparaison : libellé au centre, valeur de chaque match de part
/// et d'autre, la meilleure étant mise en évidence (vert). Une petite flèche
/// indique le sens du gain.
private struct CompareRow: View {
    enum Format { case rating, count, percent }

    let label: LocalizedStringKey
    let left: Double
    let right: Double
    let format: Format
    /// Pour des métriques où une valeur plus basse est meilleure (ex. fautes).
    var lowerIsBetter: Bool = false

    private var leftWins: Bool {
        lowerIsBetter ? left < right : left > right
    }
    private var rightWins: Bool {
        lowerIsBetter ? right < left : right > left
    }
    private var tie: Bool { abs(left - right) < 0.0001 }

    var body: some View {
        HStack(spacing: 8) {
            valueText(left, highlighted: leftWins)
                .frame(maxWidth: .infinity, alignment: .leading)

            VStack(spacing: 2) {
                Text(label)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .lineLimit(1)
                    .minimumScaleFactor(0.7)
                if !tie {
                    Image(systemName: leftWins ? "arrow.left" : "arrow.right")
                        .font(.system(size: 9))
                        .foregroundStyle(.green)
                }
            }
            .frame(width: 110)

            valueText(right, highlighted: rightWins)
                .frame(maxWidth: .infinity, alignment: .trailing)
        }
    }

    private func valueText(_ value: Double, highlighted: Bool) -> some View {
        Text(formatted(value))
            .font(.subheadline)
            .fontWeight(highlighted ? .bold : .regular)
            .foregroundStyle(highlighted ? Color.green : .primary)
    }

    private func formatted(_ value: Double) -> String {
        switch format {
        case .rating:  return String(format: "%.1f", value)
        case .count:   return String(format: "%.0f", value)
        case .percent: return String(format: "%.0f%%", value)
        }
    }
}

#Preview {
    MatchComparisonView(recordings: [])
}
