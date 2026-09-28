//
//  TrainingPlanView.swift
//  nextmove
//
//  « Programme d'entraînement » — miroir iOS de l'écran web /training-plan.
//  Le coach IA (mêmes agents RAG que le web) génère un programme personnalisé
//  à partir des matchs analysés récents de l'utilisateur. Chaque carte suit le
//  même format que le web : Constat / Analyse / Exercice recommandé / pro-tip.
//

import SwiftUI

struct TrainingPlanView: View {
    @EnvironmentObject private var api: NextMoveAPI
    @EnvironmentObject private var sportManager: SportManager

    /// Sports proposés (ceux couverts par le coach RAG côté backend).
    private let sports: [SportType] = [.padel, .pickleball, .tennis]

    @State private var sport: SportType = .padel
    @State private var plans: [TrainingPlan] = []
    @State private var isLoadingHistory = true
    @State private var isGenerating = false
    @State private var errorMessage: String?

    private var latestPlan: TrainingPlan? { plans.first }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                header
                sportSelector
                generateButton

                if let errorMessage {
                    errorBanner(errorMessage)
                }

                if isLoadingHistory {
                    Text("Loading history…")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                } else if let latestPlan, !latestPlan.content.recommandations_coach.isEmpty {
                    planCards(latestPlan)
                } else if errorMessage == nil {
                    emptyState
                }
            }
            .padding()
        }
        .navigationTitle("Training Plan")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            // Ouvre sur le sport courant de l'app s'il est couvert.
            if let current = sportManager.currentSport, sports.contains(current) {
                sport = current
            }
            Task { await loadHistory() }
        }
    }

    // MARK: - Header

    private var header: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Training Plan")
                .font(.title2)
                .fontWeight(.bold)
            Text("Generated from your recently analyzed games.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
    }

    // MARK: - Sport selector

    private var sportSelector: some View {
        HStack(spacing: 8) {
            ForEach(sports) { s in
                let isSelected = s == sport
                Button {
                    guard s != sport else { return }
                    sport = s
                    plans = []
                    isLoadingHistory = true
                    errorMessage = nil
                    Task { await loadHistory() }
                } label: {
                    HStack(spacing: 6) {
                        if let asset = s.assetIconName {
                            Image(asset).resizable().scaledToFit().frame(height: 18)
                        } else {
                            Text(s.icon)
                        }
                        Text(s.displayName)
                            .font(.subheadline)
                            .fontWeight(.medium)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .background((isSelected ? Color.green.opacity(0.15) : Color(.secondarySystemBackground)))
                    .overlay(
                        RoundedRectangle(cornerRadius: 10)
                            .stroke(isSelected ? Color.green : .clear, lineWidth: 1.5)
                    )
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                }
                .buttonStyle(.plain)
                .disabled(isGenerating)
            }
        }
    }

    // MARK: - Generate button

    private var generateButton: some View {
        Button {
            Task { await generate() }
        } label: {
            HStack {
                if isGenerating { ProgressView().tint(.white) }
                Group {
                    if isGenerating {
                        Text("Generating…")
                    } else {
                        Text("Generate a new plan")
                    }
                }
                .fontWeight(.semibold)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 14)
            .background(Color.green)
            .foregroundStyle(.white)
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .opacity(isGenerating || isLoadingHistory ? 0.6 : 1)
        }
        .disabled(isGenerating || isLoadingHistory)
    }

    // MARK: - Plan cards

    private func planCards(_ plan: TrainingPlan) -> some View {
        VStack(spacing: 12) {
            ForEach(plan.content.recommandations_coach) { rec in
                RecommendationCard(rec: rec)
            }
        }
    }

    // MARK: - States

    private func errorBanner(_ message: String) -> some View {
        Text(message)
            .font(.subheadline)
            .foregroundStyle(.orange)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, 14)
            .padding(.vertical, 10)
            .background(Color.orange.opacity(0.1))
            .clipShape(RoundedRectangle(cornerRadius: 10))
    }

    private var emptyState: some View {
        VStack(spacing: 8) {
            Text("No plan for this sport yet.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
            Text("Generate one from your analyzed games.")
                .font(.caption)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 32)
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 16))
    }

    // MARK: - Actions

    private func loadHistory() async {
        do {
            let saved = try await api.fetchTrainingPlans(sport: sport.rawValue)
            plans = saved
        } catch {
            // Pas d'historique récupérable : on repart d'une liste vide (comme le web).
            plans = []
        }
        isLoadingHistory = false
    }

    private func generate() async {
        errorMessage = nil
        isGenerating = true
        defer { isGenerating = false }
        do {
            let plan = try await api.generateTrainingPlan(sport: sport.rawValue)
            plans.insert(plan, at: 0)
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

// MARK: - Recommendation card

/// Une carte de recommandation, même structure que le web :
/// titre, Constat, Analyse, Exercice recommandé (encadré vert), pro-tip.
private struct RecommendationCard: View {
    let rec: CoachRecommendation

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(rec.titre)
                .font(.subheadline)
                .fontWeight(.semibold)

            labeled("Observation", rec.contenu.constat)
            labeled("Analysis", rec.contenu.analyse)

            (Text("Recommended drill — ").fontWeight(.medium).foregroundColor(.green)
             + Text(rec.contenu.action_corrective))
                .font(.footnote)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(10)
                .background(Color.green.opacity(0.1))
                .clipShape(RoundedRectangle(cornerRadius: 10))

            if let tip = rec.contenu.pro_tip, !tip.isEmpty {
                Text("💡 \(tip)")
                    .font(.footnote)
                    .italic()
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .shadow(color: .black.opacity(0.05), radius: 8, y: 4)
    }

    private func labeled(_ label: LocalizedStringKey, _ value: String) -> some View {
        (Text(label).fontWeight(.medium).foregroundColor(.secondary)
         + Text(verbatim: " — ").foregroundColor(.secondary)
         + Text(value).foregroundColor(.primary))
            .font(.footnote)
            .frame(maxWidth: .infinity, alignment: .leading)
    }
}

#Preview {
    NavigationStack {
        TrainingPlanView()
            .environmentObject(NextMoveAPI())
            .environmentObject(SportManager())
    }
}
