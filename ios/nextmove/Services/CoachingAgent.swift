//
//  CoachingAgent.swift
//  nextmove
//
//  Conversational AI coach. Answers player questions and gives personalized
//  recommendations grounded in the analysis of a specific game.
//
//  Falls back to a rule-based coach when no LLM API key is configured, so the
//  feature always works (offline/demo safe).
//

import Foundation

// MARK: - Chat Message

/// A single message in a coaching conversation.
struct CoachChatMessage: Identifiable, Codable, Equatable {
    enum Role: String, Codable {
        case user
        case coach
    }

    let id: UUID
    let role: Role
    let text: String
    let timestamp: Date

    init(id: UUID = UUID(), role: Role, text: String, timestamp: Date = Date()) {
        self.id = id
        self.role = role
        self.text = text
        self.timestamp = timestamp
    }
}

// MARK: - Coaching Agent

/// A conversational coach that reasons over a game's analysis.
///
/// Usage:
/// ```swift
/// let agent = CoachingAgent(sportType: .pickleball, analysis: analysis, feedback: feedback)
/// let reply = try await agent.send("How do I fix my positioning?")
/// ```
final class CoachingAgent {

    private let sportType: SportType
    private let analysis: GameAnalysis?
    private let feedback: CoachingFeedback?
    private let llmService: LLMService
    private let config = ConfigurationManager.shared

    /// Full conversation history (includes the opening message).
    private(set) var history: [CoachChatMessage] = []

    private var useLLM: Bool {
        config.openAIAPIKey != nil
    }

    init(
        sportType: SportType,
        analysis: GameAnalysis?,
        feedback: CoachingFeedback? = nil,
        llmService: LLMService = LLMService()
    ) {
        self.sportType = sportType
        self.analysis = analysis
        self.feedback = feedback
        self.llmService = llmService
    }

    // MARK: - Public API

    /// Generates the coach's opening message for a session.
    func greeting() -> CoachChatMessage {
        let sport = sportType.displayName
        let text: String
        if let analysis {
            let rating = String(format: "%.1f", analysis.overallRating)
            text = "Hey! I'm your \(sport) coach. I reviewed your game — you're sitting at \(rating)/5.0 overall. "
                + "Ask me anything: what to work on, drills for a weak shot, or how to win more points. What's on your mind?"
        } else {
            text = "Hey! I'm your \(sport) coach. Analyze a game and I can give you tailored feedback. "
                + "In the meantime, ask me anything about your technique or strategy."
        }
        let message = CoachChatMessage(role: .coach, text: text)
        history.append(message)
        return message
    }

    /// Sends a user message and returns the coach's reply.
    /// Uses the LLM when configured, otherwise a rule-based response.
    @discardableResult
    func send(_ userText: String) async throws -> CoachChatMessage {
        let trimmed = userText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            throw CoachingAgentError.emptyMessage
        }

        history.append(CoachChatMessage(role: .user, text: trimmed))

        let replyText: String
        if useLLM {
            do {
                replyText = try await generateLLMReply(to: trimmed)
            } catch {
                // Never break the conversation — degrade to rule-based.
                replyText = ruleBasedReply(to: trimmed)
            }
        } else {
            replyText = ruleBasedReply(to: trimmed)
        }

        let reply = CoachChatMessage(role: .coach, text: replyText)
        history.append(reply)
        return reply
    }

    // MARK: - LLM Path

    private func generateLLMReply(to userText: String) async throws -> String {
        let systemContext = buildSystemContext()
        // Encode recent conversation so the coach has memory of the exchange.
        let transcript = history.suffix(10).map { msg -> String in
            let speaker = msg.role == .user ? "Player" : "Coach"
            return "\(speaker): \(msg.text)"
        }.joined(separator: "\n")

        let performanceData = """
        \(systemContext)

        Conversation so far:
        \(transcript)

        Respond as the coach to the player's latest message. Keep it to 2-4 sentences,
        specific and encouraging, and reference the player's actual stats when relevant.
        """

        return try await llmService.generateCoachingInsights(
            performanceData: performanceData,
            sportType: sportType.displayName,
            temperature: 0.7
        )
    }

    /// Builds a compact, factual summary of the game for grounding the LLM.
    private func buildSystemContext() -> String {
        guard let analysis else {
            return "No game analysis is available yet for this \(sportType.displayName) player."
        }

        let s = analysis.statistics
        let r = analysis.skillRatings

        var context = "Game analysis for a \(sportType.displayName) player:\n"
        context += "- Overall rating: \(String(format: "%.1f", analysis.overallRating))/5.0\n"
        context += "- Skill ratings (0-5): dinking \(fmt(r.dinking)), volleys \(fmt(r.volleys)), "
        context += "movement \(fmt(r.movement)), serve \(fmt(r.serve)), return \(fmt(r.return)), thirdShot \(fmt(r.thirdShot))\n"
        context += "- Rallies: \(s.totalRallies), longest \(s.longestRally) shots\n"
        context += "- Winners: \(s.winners), unforced errors: \(s.errors)\n"
        context += "- Court coverage: \(Int(s.courtCoveragePercent))%\n"

        if let feedback, !feedback.insights.isEmpty {
            context += "Detected issues: "
            context += feedback.insights.prefix(3).map { $0.title }.joined(separator: ", ")
            context += "\n"
        }
        return context
    }

    // MARK: - Rule-Based Path (offline / no API key)

    /// Produces a helpful, grounded reply without an LLM by matching intent keywords.
    private func ruleBasedReply(to userText: String) -> String {
        let text = userText.lowercased()

        // Intent: what should I work on / weakness
        if text.contains("work on") || text.contains("weak") || text.contains("improve") || text.contains("focus") {
            return weakestSkillAdvice()
        }
        // Intent: drills / practice
        if text.contains("drill") || text.contains("practice") || text.contains("train") {
            return drillAdvice()
        }
        // Intent: strengths / what am I good at
        if text.contains("good") || text.contains("strength") || text.contains("best") {
            return strengthAdvice()
        }
        // Intent: winning more / strategy
        if text.contains("win") || text.contains("strategy") || text.contains("point") || text.contains("beat") {
            return strategyAdvice()
        }
        // Intent: errors / mistakes
        if text.contains("error") || text.contains("mistake") || text.contains("miss") {
            return errorAdvice()
        }
        // Intent: overall / how did i do
        if text.contains("how did") || text.contains("overall") || text.contains("rating") || text.contains("summary") {
            return summaryAdvice()
        }

        // Fallback: point them at their top issue.
        return weakestSkillAdvice()
    }

    private func weakestSkillAdvice() -> String {
        guard let r = analysis?.skillRatings else {
            return "Once you analyze a game I can pinpoint your weakest shot. Generally in \(sportType.displayName), controlling the net and keeping the ball low wins points."
        }
        let skills: [(String, Double, String)] = [
            ("dinking", r.dinking, "Soften your grip and aim for the top of the net — controlled dinks force errors."),
            ("volleys", r.volleys, "Punch the ball with a firm wrist and short backswing; keep the paddle out in front."),
            ("movement", r.movement, "Split-step as your opponent hits and recover to the middle after every shot."),
            ("serve", r.serve, "Focus on depth and consistency before power — a deep serve pushes opponents back."),
            ("return", r.return, "Return deep and get to the net; a deep return buys you time to move up."),
            ("thirdShot", r.thirdShot, "Practice the third-shot drop: arc it into the kitchen so you can move forward safely.")
        ]
        if let weakest = skills.min(by: { $0.1 < $1.1 }) {
            return "Your \(weakest.0) is your biggest opportunity right now (\(fmt(weakest.1))/5.0). \(weakest.2)"
        }
        return "Keep working the fundamentals — net control and consistency win \(sportType.displayName) points."
    }

    private func strengthAdvice() -> String {
        guard let r = analysis?.skillRatings else {
            return "Analyze a game and I'll tell you exactly what's working. Lean on your strengths to set up points."
        }
        let skills: [(String, Double)] = [
            ("dinking", r.dinking), ("volleys", r.volleys), ("movement", r.movement),
            ("serve", r.serve), ("return", r.return), ("third shot", r.thirdShot)
        ]
        if let best = skills.max(by: { $0.1 < $1.1 }) {
            return "Your \(best.0) is a real strength (\(fmt(best.1))/5.0). Build your game plan around it — use it to pressure opponents and open up the court."
        }
        return "You've got a well-rounded game. Keep sharpening consistency and you'll climb fast."
    }

    private func drillAdvice() -> String {
        if let feedback, let suggestion = feedback.practiceSuggestions.first {
            return "Try the \(suggestion.drill): \(suggestion.description)"
        }
        if sportType == .padel {
            return "Great padel drill: practice the volley-off-the-wall. Let the ball rebound and take it early to stay aggressive at the net."
        }
        return "Great drill: the dink-and-recover. Dink cross-court, then recover to the kitchen line before the next ball. Do 20 reps each side."
    }

    private func strategyAdvice() -> String {
        guard let s = analysis?.statistics else {
            return "In \(sportType.displayName), the team that controls the net usually wins. Get to the kitchen line and keep the ball low."
        }
        if s.errors > s.winners {
            return "You had \(s.errors) unforced errors vs \(s.winners) winners. To win more, cut the errors first — play higher-percentage shots and keep the ball in until your opponent misses."
        }
        return "You're generating winners (\(s.winners) vs \(s.errors) errors) — nice. Keep pressuring the net and finish points when you get a ball above the net."
    }

    private func errorAdvice() -> String {
        guard let s = analysis?.statistics else {
            return "Reduce errors by aiming bigger targets — a few feet inside the lines — and only attacking balls above net height."
        }
        return "You made \(s.errors) unforced errors this game. Most come from attacking low balls. Reset with a dink when the ball is below the net, and only speed it up when you get one high."
    }

    private func summaryAdvice() -> String {
        guard let analysis else {
            return "Analyze a game and I'll give you a full breakdown of your \(sportType.displayName) performance."
        }
        let s = analysis.statistics
        return "Overall you're at \(fmt(analysis.overallRating))/5.0. You played \(s.totalRallies) rallies with \(s.winners) winners and \(s.errors) errors, covering \(Int(s.courtCoveragePercent))% of the court. Ask me what to work on and I'll get specific."
    }

    private func fmt(_ value: Double) -> String {
        String(format: "%.1f", value)
    }
}

// MARK: - Errors

enum CoachingAgentError: Error, LocalizedError {
    case emptyMessage

    var errorDescription: String? {
        switch self {
        case .emptyMessage:
            return "Message cannot be empty."
        }
    }
}
