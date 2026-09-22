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

    /// Suggested prompts shown to the user to kick off the conversation.
    let suggestedPrompts: [String] = [
        "What should I work on?",
        "Give me a drill",
        "How do I win more points?",
        "What am I good at?"
    ]

    init(sportType: SportType, analysis: GameAnalysis?, feedback: CoachingFeedback? = nil) {
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

        do {
            let reply = try await agent.send(trimmed)
            messages.append(reply)
        } catch {
            messages.append(CoachChatMessage(
                role: .coach,
                text: "Sorry, I couldn't respond just now. Try asking again."
            ))
        }

        isThinking = false
    }
}
