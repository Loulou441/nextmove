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

    /// Backend API client and the server-side match id. When BOTH are set, the
    /// coach routes questions through the FastAPI `/matches/{id}/chat` endpoint,
    /// which runs the SAME moderator (prompt-injection + off-topic) and RAG as
    /// the web. This is the preferred path: one shared guard for both platforms
    /// and no LLM key on the device. When they're absent (offline, demo, or a
    /// game not yet synced to the server), the coach falls back to the local
    /// path, still protected by the on-device InjectionGuard / TopicGuard.
    private let api: NextMoveAPI?
    private let matchId: String?

    /// The language the coach must answer in ("en"/"fr"), captured when the
    /// chat opens. Passed explicitly to both the local LLM and the backend so
    /// the reply language never depends on a global read from a background task.
    private let languageCode: String

    /// Full conversation history (includes the opening message).
    private(set) var history: [CoachChatMessage] = []

    private var useBackend: Bool {
        api != nil && matchId != nil
    }

    private var useLLM: Bool {
        config.openAIAPIKey != nil
    }

    init(
        sportType: SportType,
        analysis: GameAnalysis?,
        feedback: CoachingFeedback? = nil,
        llmService: LLMService = LLMService(),
        api: NextMoveAPI? = nil,
        matchId: String? = nil,
        languageCode: String = LanguageManager.currentLanguage.llmLanguageCode
    ) {
        self.sportType = sportType
        self.analysis = analysis
        self.feedback = feedback
        self.llmService = llmService
        self.api = api
        self.matchId = matchId
        self.languageCode = languageCode
    }

    // MARK: - Public API

    /// Generates the coach's opening message for a session.
    func greeting() -> CoachChatMessage {
        let sport = sportType.displayName
        let text: String
        if let analysis {
            let rating = String(format: "%.1f", analysis.overallRating)
            text = appLocalized("Hey! I'm your %@ coach. I reviewed your game — you're sitting at %@/5.0 overall. Ask me anything: what to work on, drills for a weak shot, or how to win more points. What's on your mind?", sport, rating)
        } else {
            text = appLocalized("Hey! I'm your %@ coach. Analyze a game and I can give you tailored feedback. In the meantime, ask me anything about your technique or strategy.", sport)
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

        // Conversation so far, BEFORE this turn — the backend appends the new
        // message itself, so we must not include it in the history we send.
        let priorHistory = history
        history.append(CoachChatMessage(role: .user, text: trimmed))

        // Preferred path: route through the backend so the SAME server-side
        // moderator (prompt-injection + off-topic) and RAG the web uses apply
        // here too. If the server is reachable, its moderation is authoritative
        // and we do NOT fall back to the local LLM (that would defeat the
        // guard). We only fall back to the local coach on connectivity/parse
        // failures, so the conversation never breaks offline.
        if useBackend, let api, let matchId {
            do {
                let replyText = try await api.chatWithCoach(
                    matchId: matchId,
                    message: trimmed,
                    history: priorHistory,
                    languageCode: languageCode
                )
                let reply = CoachChatMessage(role: .coach, text: replyText)
                history.append(reply)
                return reply
            } catch APIError.server(let detail) {
                // The moderator blocked the message (HTTP 400) or the server
                // returned another handled error. Surface its message verbatim
                // instead of answering locally — this is the guard doing its job.
                let reply = CoachChatMessage(role: .coach, text: detail)
                history.append(reply)
                return reply
            } catch APIError.unauthorized {
                // Session expired — fall through to the local, guarded path.
            } catch {
                // Network/timeout/decoding issue — degrade gracefully below.
            }
        }

        // Local fallback path (offline, demo, unsynced game, or server
        // unreachable). Still protected by the on-device guards below.

        // Prompt-injection guard (mirrors the backend moderator): block attempts
        // to reconfigure/override the coach before anything else, exactly like
        // the web moderator checks injection first. Runs BEFORE any LLM call so
        // it works offline and can't be bypassed by the model itself.
        if InjectionGuard.isPromptInjection(trimmed) {
            let reply = CoachChatMessage(role: .coach, text: injectionBlockedMessage())
            history.append(reply)
            return reply
        }

        // Topic guard (mirrors the backend moderator's off-topic check): the
        // coach only answers sport/performance questions. This runs BEFORE any
        // LLM call, so it works offline and can't be bypassed by the model
        // drifting off-topic. On-topic-when-in-doubt: we only redirect a
        // message we're confident is unrelated to the player's sport.
        if TopicGuard.isOffTopic(trimmed) {
            let reply = CoachChatMessage(role: .coach, text: offTopicRedirect())
            history.append(reply)
            return reply
        }

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
        // Prior conversation, excluding the just-appended user message (passed
        // separately as the question). Maps to (isCoach, text) pairs.
        let priorTurns = history.dropLast().map { (isCoach: $0.role == .coach, text: $0.text) }

        // Use the CONVERSATIONAL coach method so the reply actually answers the
        // player's question, instead of the fixed "report" template that the
        // insights generator produces.
        let languageName = languageCode.hasPrefix("fr") ? "French" : "English"
        return try await llmService.chatReply(
            gameContext: buildSystemContext(),
            conversation: priorTurns,
            question: userText,
            sportType: sportType.displayName,
            language: languageName
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

        func matches(_ keywords: [String]) -> Bool {
            keywords.contains { text.contains($0) }
        }

        // Intent: what should I work on / weakness (EN + FR keywords)
        if matches(["work on", "weak", "improve", "focus",
                    "travailler", "faible", "améliorer", "progresser", "point faible"]) {
            return weakestSkillAdvice()
        }
        // Intent: drills / practice
        if matches(["drill", "practice", "train",
                    "exercice", "entraîn", "entrain", "s'entraîner"]) {
            return drillAdvice()
        }
        // Intent: strengths / what am I good at
        if matches(["good", "strength", "best",
                    "fort", "point fort", "meilleur", "doué", "bon"]) {
            return strengthAdvice()
        }
        // Intent: winning more / strategy
        if matches(["win", "strategy", "point", "beat",
                    "gagner", "stratégie", "strategie", "tactique", "battre"]) {
            return strategyAdvice()
        }
        // Intent: errors / mistakes
        if matches(["error", "mistake", "miss",
                    "erreur", "faute", "rater", "manqu"]) {
            return errorAdvice()
        }
        // Intent: overall / how did i do
        if matches(["how did", "overall", "rating", "summary",
                    "globale", "résumé", "resume", "bilan", "note", "comment j'ai"]) {
            return summaryAdvice()
        }

        // Fallback: point them at their top issue.
        return weakestSkillAdvice()
    }

    private func weakestSkillAdvice() -> String {
        let sport = sportType.displayName
        guard let r = analysis?.skillRatings else {
            return String(localized: "Once you analyze a game I can pinpoint your weakest shot. Generally in \(sport), controlling the net and keeping the ball low wins points.")
        }
        // (skillKey, rating, localized skill name, localized advice)
        let skills: [(Double, String, String)] = [
            (r.dinking, String(localized: "dinking"), String(localized: "Soften your grip and aim for the top of the net — controlled dinks force errors.")),
            (r.volleys, String(localized: "volleys"), String(localized: "Punch the ball with a firm wrist and short backswing; keep the paddle out in front.")),
            (r.movement, String(localized: "movement"), String(localized: "Split-step as your opponent hits and recover to the middle after every shot.")),
            (r.serve, String(localized: "serve"), String(localized: "Focus on depth and consistency before power — a deep serve pushes opponents back.")),
            (r.return, String(localized: "return"), String(localized: "Return deep and get to the net; a deep return buys you time to move up.")),
            (r.thirdShot, String(localized: "third shot"), String(localized: "Practice the third-shot drop: arc it into the kitchen so you can move forward safely."))
        ]
        if let weakest = skills.min(by: { $0.0 < $1.0 }) {
            let skill = weakest.1
            let value = fmt(weakest.0)
            let tip = weakest.2
            return String(localized: "Your \(skill) is your biggest opportunity right now (\(value)/5.0). \(tip)")
        }
        return String(localized: "Keep working the fundamentals — net control and consistency win \(sport) points.")
    }

    private func strengthAdvice() -> String {
        guard let r = analysis?.skillRatings else {
            return String(localized: "Analyze a game and I'll tell you exactly what's working. Lean on your strengths to set up points.")
        }
        let skills: [(Double, String)] = [
            (r.dinking, String(localized: "dinking")), (r.volleys, String(localized: "volleys")), (r.movement, String(localized: "movement")),
            (r.serve, String(localized: "serve")), (r.return, String(localized: "return")), (r.thirdShot, String(localized: "third shot"))
        ]
        if let best = skills.max(by: { $0.0 < $1.0 }) {
            let skill = best.1
            let value = fmt(best.0)
            return String(localized: "Your \(skill) is a real strength (\(value)/5.0). Build your game plan around it — use it to pressure opponents and open up the court.")
        }
        return String(localized: "You've got a well-rounded game. Keep sharpening consistency and you'll climb fast.")
    }

    private func drillAdvice() -> String {
        if let feedback, let suggestion = feedback.practiceSuggestions.first {
            let drill = suggestion.drill
            let description = suggestion.description
            return String(localized: "Try the \(drill): \(description)")
        }
        if sportType == .padel {
            return String(localized: "Great padel drill: practice the volley-off-the-wall. Let the ball rebound and take it early to stay aggressive at the net.")
        }
        return String(localized: "Great drill: the dink-and-recover. Dink cross-court, then recover to the kitchen line before the next ball. Do 20 reps each side.")
    }

    private func strategyAdvice() -> String {
        let sport = sportType.displayName
        guard let s = analysis?.statistics else {
            return String(localized: "In \(sport), the team that controls the net usually wins. Get to the kitchen line and keep the ball low.")
        }
        if s.errors > s.winners {
            let errors = s.errors
            let winners = s.winners
            return String(localized: "You had \(errors) unforced errors vs \(winners) winners. To win more, cut the errors first — play higher-percentage shots and keep the ball in until your opponent misses.")
        }
        let winners = s.winners
        let errors = s.errors
        return String(localized: "You're generating winners (\(winners) vs \(errors) errors) — nice. Keep pressuring the net and finish points when you get a ball above the net.")
    }

    private func errorAdvice() -> String {
        guard let s = analysis?.statistics else {
            return String(localized: "Reduce errors by aiming bigger targets — a few feet inside the lines — and only attacking balls above net height.")
        }
        let errors = s.errors
        return String(localized: "You made \(errors) unforced errors this game. Most come from attacking low balls. Reset with a dink when the ball is below the net, and only speed it up when you get one high.")
    }

    private func summaryAdvice() -> String {
        let sport = sportType.displayName
        guard let analysis else {
            return String(localized: "Analyze a game and I'll give you a full breakdown of your \(sport) performance.")
        }
        let s = analysis.statistics
        let rating = fmt(analysis.overallRating)
        let rallies = s.totalRallies
        let winners = s.winners
        let errors = s.errors
        let coverage = Int(s.courtCoveragePercent)
        return String(localized: "Overall you're at \(rating)/5.0. You played \(rallies) rallies with \(winners) winners and \(errors) errors, covering \(coverage)% of the court. Ask me what to work on and I'll get specific.")
    }

    private func fmt(_ value: Double) -> String {
        String(format: "%.1f", value)
    }

    /// Polite redirect returned when a question is unrelated to the player's sport.
    private func offTopicRedirect() -> String {
        let sport = sportType.displayName
        return "I'm your \(sport) coach, so I can only help with your game — technique, tactics, "
            + "fitness, mindset, gear, or what to work on next. Ask me something about your \(sport) and I've got you."
    }

    /// Message returned when a message looks like an attempt to manipulate the coach.
    private func injectionBlockedMessage() -> String {
        "That looks like an attempt to change how I work rather than a coaching question. "
            + "I'm here to help with your \(sportType.displayName) — ask me about your technique, tactics, or what to work on."
    }
}

// MARK: - Topic Guard

/// Deterministic, offline topic filter for the conversational coach.
///
/// This is the client-side counterpart to the backend moderator's `off_topic`
/// check. It is intentionally conservative: it only flags a message as
/// off-topic when there is clear evidence it is unrelated to the player's
/// sport (e.g. recipes, weather, coding, general knowledge) AND no sports
/// vocabulary is present. When in doubt, the message is treated as on-topic so
/// legitimate coaching questions are never blocked.
enum TopicGuard {

    /// Words that strongly indicate a sports/performance/coaching question.
    /// If any appears, we always treat the message as on-topic.
    private static let sportKeywords: Set<String> = [
        // sports
        "padel", "pickleball", "tennis", "badminton", "racket", "racquet", "paddle",
        // coaching / performance
        "serve", "return", "volley", "dink", "smash", "backhand", "forehand", "grip",
        "footwork", "movement", "positioning", "position", "net", "kitchen", "rally",
        "rallies", "winner", "winners", "error", "errors", "fault", "drill", "drills",
        "practice", "train", "training", "technique", "tactic", "tactics", "strategy",
        "match", "game", "set", "point", "points", "score", "shot", "shots", "swing",
        "coach", "coaching", "improve", "weakness", "strength", "fitness", "stamina",
        "endurance", "warmup", "warm", "stretch", "injury", "recovery", "mindset",
        "focus", "opponent", "court", "baseline", "lob", "slice", "spin", "rating",
        "performance", "play", "player", "win", "beat", "defense", "attack"
    ]

    /// Words that strongly indicate an off-topic request. Used only as a
    /// tie-breaker when NO sport keyword is present.
    private static let offTopicKeywords: Set<String> = [
        "recipe", "cook", "cooking", "bake", "cake", "pizza", "weather", "forecast",
        "stock", "stocks", "crypto", "bitcoin", "invest", "president", "election",
        "politics", "poem", "essay", "translate", "translation", "capital",
        "movie", "film", "song", "lyrics", "joke", "horoscope", "news",
        "code", "python", "javascript", "swift", "sql", "html", "program", "script",
        "homework", "math", "history", "geography", "restaurant", "flight", "hotel"
    ]

    /// Returns true when the message is confidently unrelated to the player's sport.
    static func isOffTopic(_ message: String) -> Bool {
        let tokens = tokenize(message)
        guard !tokens.isEmpty else { return false }

        // Any sports/coaching vocabulary => on-topic (fail open for coaching).
        if !tokens.isDisjoint(with: sportKeywords) {
            return false
        }

        // No sport vocabulary AND at least one clear off-topic marker => block.
        if !tokens.isDisjoint(with: offTopicKeywords) {
            return true
        }

        // Ambiguous (no sport words, no off-topic markers): stay on-topic.
        // These are typically short follow-ups like "why?", "and then?",
        // "tell me more" that belong to the ongoing coaching conversation.
        return false
    }

    private static func tokenize(_ message: String) -> Set<String> {
        let lowered = message.lowercased()
        let separators = CharacterSet.alphanumerics.inverted
        let parts = lowered.components(separatedBy: separators).filter { !$0.isEmpty }
        return Set(parts)
    }
}

// MARK: - Injection Guard

/// Deterministic, offline prompt-injection filter for the conversational coach.
///
/// Client-side counterpart to the backend moderator's `is_prompt_injection`
/// check. The iOS coach talks to the LLM directly (no server moderator in the
/// loop), so this guard runs on-device before any network call and cannot be
/// bypassed by the model. It mirrors the categories the web moderator blocks:
///
///  - instructions to ignore / override / bypass the coach's rules,
///  - attempts to change the coach's role, persona or output format,
///  - requests to reveal / repeat / translate the system prompt,
///  - injection of fake system/role tags or delimiters,
///  - requests to execute external actions instead of coaching.
///
/// It matches on phrasing (not single keywords) and, like the web moderator,
/// errs toward letting legitimate-but-unusual coaching questions through.
enum InjectionGuard {

    /// Case-insensitive substring patterns that indicate a manipulation attempt.
    private static let patterns: [String] = [
        // ignore / override / bypass instructions
        "ignore the previous", "ignore previous", "ignore all previous",
        "ignore your instructions", "ignore your previous", "ignore prior",
        "disregard the previous", "disregard previous", "disregard your instructions",
        "forget your instructions", "forget the previous", "forget everything",
        "forget your context", "override your", "bypass your",
        // role / persona / format reconfiguration
        "you are now", "from now on you", "from now on, you", "act as",
        "pretend to be", "pretend you are", "roleplay as", "you must now",
        "your new role", "new instructions:", "new system prompt",
        "respond as if", "ignore the format", "stop being",
        // reveal / repeat internal prompt
        "system prompt", "reveal your prompt", "repeat your instructions",
        "show me your instructions", "what is your system", "print your prompt",
        "reveal your instructions", "your initial instructions",
        // fake system / role tags & delimiters
        "[system]", "<system>", "###system", "system:", "assistant:",
        "<|im_start|>", "<|im_end|>", "begin system",
        // external action execution
        "run this command", "execute the following", "call this url",
        "make a request to", "send an http"
    ]

    /// Returns true when the message looks like a prompt-injection attempt.
    static func isPromptInjection(_ message: String) -> Bool {
        let lowered = message.lowercased()
        for pattern in patterns where lowered.contains(pattern) {
            return true
        }
        return false
    }
}

// MARK: - Errors

enum CoachingAgentError: Error, LocalizedError {
    case emptyMessage

    var errorDescription: String? {
        switch self {
        case .emptyMessage:
            return String(localized: "Message cannot be empty.")
        }
    }
}
