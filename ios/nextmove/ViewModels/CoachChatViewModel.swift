//
//  CoachChatViewModel.swift
//  nextmove
//
//  Drives the conversational coaching UI.
//

import Foundation
import SwiftUI
import Combine

@MainActor
final class CoachChatViewModel: ObservableObject {
    @Published var messages: [CoachChatMessage] = []
    @Published var inputText: String = ""
    @Published var isThinking: Bool = false

    private let agent: CoachingAgent

    /// Shared backend client. When logged in, we route coaching through the
    /// backend RAG agents (same brain as the web app); otherwise we fall back
    /// to the on-device CoachingAgent.
    private let api: NextMoveAPI?
    private let sportType: SportType
    private let analysis: GameAnalysis?
    /// Whether we've already fetched the RAG plan for this session (once is enough).
    private var didFetchRAGPlan = false

    /// Suggested prompts shown to the user to kick off the conversation.
    let suggestedPrompts: [String] = [
        "What should I work on?",
        "Give me a drill",
        "How do I win more points?",
        "What am I good at?"
    ]

    init(sportType: SportType, analysis: GameAnalysis?, feedback: CoachingFeedback? = nil, api: NextMoveAPI? = nil) {
        self.sportType = sportType
        self.analysis = analysis
        self.api = api
        self.agent = CoachingAgent(sportType: sportType, analysis: analysis, feedback: feedback)
        // Seed with the coach's greeting.
        messages = [agent.greeting()]
    }

    var canSend: Bool {
        !inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && !isThinking
    }

    func send() {
        let text = inputText
        inputText = ""
        Task { await deliver(text) }
    }

    func sendSuggested(_ prompt: String) {
        Task { await deliver(prompt) }
    }

    private func deliver(_ text: String) async {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }

        // Optimistically show the user's message.
        messages.append(CoachChatMessage(role: .user, text: trimmed))
        isThinking = true

        // 1) Groq drives the conversation (on-device LLM, or rule-based if no key).
        var replyText: String
        do {
            replyText = try await agent.send(trimmed).text
        } catch {
            replyText = "Sorry, I couldn't respond just now. Try asking again."
            messages.append(CoachChatMessage(role: .coach, text: replyText))
            isThinking = false
            return
        }

        // 2) RAG is a KNOWLEDGE BASE: enrich the answer with real, validated drills
        //    when the ask is drill/plan-oriented. It augments — never replaces — the
        //    Groq answer, and is skipped silently if unavailable.
        if let drills = await fetchRAGDrills(for: trimmed) {
            replyText += "\n\n" + drills
        }

        messages.append(CoachChatMessage(role: .coach, text: replyText))
        isThinking = false
    }

    /// Retrieves grounded drill references from the backend RAG knowledge base to
    /// ENRICH the Groq answer. Returns a formatted "recommended drills" block, or
    /// nil when it shouldn't/can't augment (no session, no analysis, off-topic,
    /// already added this session, or backend error).
    private func fetchRAGDrills(for userText: String) async -> String? {
        guard let api, api.isLoggedIn, let analysis else { return nil }

        // Only enrich drill/plan-style asks; keep quick chit-chat lightweight.
        // Augment at most once per session to avoid repeating the same drills.
        let t = userText.lowercased()
        let wantsDrills = t.contains("plan") || t.contains("work on") || t.contains("drill")
            || t.contains("improve") || t.contains("recommend") || t.contains("practice")
            || t.contains("exercise")
        guard wantsDrills, !didFetchRAGPlan else { return nil }

        let sequences = Self.buildSequences(from: analysis, sport: sportType)
        guard !sequences.isEmpty else { return nil }

        do {
            let response = try await api.fetchCoachRecommendations(
                sport: sportType.rawValue,
                sequences: sequences
            )
            didFetchRAGPlan = true
            return Self.formatDrills(response)
        } catch {
            // Backend unavailable / unauthorized / timeout — enrich nothing.
            return nil
        }
    }

    /// Maps the game's highlights into coaching sequences the RAG agents expect.
    private static func buildSequences(from analysis: GameAnalysis, sport: SportType) -> [CoachSequenceInput] {
        // Use highlights as the key events; if none, synthesize one from stats.
        if !analysis.highlights.isEmpty {
            return analysis.highlights.prefix(5).map { h in
                CoachSequenceInput(
                    timestamp: Self.mmss(h.timestamp),
                    evenement_cle: h.description,
                    contexte_tactique: "\(h.type.rawValue) during a \(sport.displayName) rally.",
                    metriques_video: ["type": h.type.rawValue]
                )
            }
        }
        let s = analysis.statistics
        return [
            CoachSequenceInput(
                timestamp: "00:00",
                evenement_cle: "Overall game review",
                contexte_tactique: "\(s.totalRallies) rallies, \(s.winners) winners, \(s.errors) errors, coverage \(Int(s.courtCoveragePercent))%.",
                metriques_video: ["rating": String(format: "%.1f", analysis.overallRating)]
            )
        ]
    }

    /// Formats RAG results as a grounded "recommended drills" block that
    /// augments the Groq answer (knowledge-base references, not a full plan).
    private static func formatDrills(_ response: CoachRecommendationsResponse) -> String {
        guard !response.recommandations_coach.isEmpty else { return "" }
        var out = "📚 Recommended drills from the knowledge base:"
        for rec in response.recommandations_coach.prefix(3) {
            out += "\n• \(rec.titre): \(rec.contenu.action_corrective)"
        }
        return out.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private static func mmss(_ seconds: TimeInterval) -> String {
        let m = Int(seconds) / 60, s = Int(seconds) % 60
        return String(format: "%02d:%02d", m, s)
    }
}
