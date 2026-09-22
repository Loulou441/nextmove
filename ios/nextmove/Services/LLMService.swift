//
//  LLMService.swift
//  nextmove
//
//  Handles communication with OpenAI-compatible LLM APIs
//

import Foundation

enum LLMError: Error {
    case missingAPIKey
    case invalidURL
    case invalidResponse
    case apiError(String)
    case networkError(Error)
}

struct LLMMessage: Codable {
    let role: String
    let content: String
}

struct LLMRequest: Codable {
    let model: String
    let messages: [LLMMessage]
    let temperature: Double
    let maxTokens: Int?
    
    enum CodingKeys: String, CodingKey {
        case model
        case messages
        case temperature
        case maxTokens = "max_tokens"
    }
}

struct LLMResponse: Codable {
    let id: String
    let choices: [Choice]
    
    struct Choice: Codable {
        let message: LLMMessage
        let finishReason: String?
        
        enum CodingKeys: String, CodingKey {
            case message
            case finishReason = "finish_reason"
        }
    }
}

class LLMService {
    private let config = ConfigurationManager.shared
    private let session: URLSession
    
    init(session: URLSession = .shared) {
        self.session = session
    }
    
    func generateCoachingInsights(
        performanceData: String,
        sportType: String,
        temperature: Double = 0.7
    ) async throws -> String {
        guard let apiKey = config.openAIAPIKey else {
            throw LLMError.missingAPIKey
        }
        
        let systemPrompt = """
        You are an expert \(sportType) coach providing personalized feedback based on video analysis data.
        
        Your role:
        - Analyze performance metrics and identify key areas for improvement
        - Provide clear, actionable coaching advice in plain language
        - Prioritize the most impactful issues
        - Be encouraging and constructive
        - Keep feedback concise and focused
        
        Format your response as:
        1. Top 3 insights (title + description)
        2. Practice suggestions (specific drills)
        3. Quick tips (immediate actions)
        4. Next session focus areas
        """
        
        let userPrompt = """
        Analyze this performance data and provide coaching feedback:
        
        \(performanceData)
        
        Generate comprehensive coaching feedback following the format specified.
        """
        
        let messages = [
            LLMMessage(role: "system", content: systemPrompt),
            LLMMessage(role: "user", content: userPrompt)
        ]
        
        return try await sendRequest(messages: messages, temperature: temperature)
    }
    
    func enhanceCoachingDescription(
        issueType: String,
        metrics: String,
        confidence: Double,
        sportType: String
    ) async throws -> String {
        guard let apiKey = config.openAIAPIKey else {
            throw LLMError.missingAPIKey
        }
        
        let systemPrompt = """
        You are a \(sportType) coach explaining a specific performance issue.
        Provide a clear, encouraging explanation in 2-3 sentences.
        Use confidence level to adjust language: high confidence = direct, medium = qualifying language.
        """
        
        let userPrompt = """
        Issue: \(issueType)
        Metrics: \(metrics)
        Confidence: \(String(format: "%.1f%%", confidence * 100))
        
        Explain this issue in plain language for the player.
        """
        
        let messages = [
            LLMMessage(role: "system", content: systemPrompt),
            LLMMessage(role: "user", content: userPrompt)
        ]
        
        return try await sendRequest(messages: messages, temperature: 0.7)
    }
    
    private func sendRequest(
        messages: [LLMMessage],
        temperature: Double,
        maxTokens: Int? = 1000
    ) async throws -> String {
        guard let apiKey = config.openAIAPIKey else {
            throw LLMError.missingAPIKey
        }
        
        let baseURL = config.openAIBaseURL
        guard let url = URL(string: "\(baseURL)/chat/completions") else {
            throw LLMError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        
        if let orgID = config.openAIOrgID {
            request.setValue(orgID, forHTTPHeaderField: "OpenAI-Organization")
        }
        
        let llmRequest = LLMRequest(
            model: config.openAIModel,
            messages: messages,
            temperature: temperature,
            maxTokens: maxTokens
        )
        
        request.httpBody = try JSONEncoder().encode(llmRequest)
        
        do {
            let (data, response) = try await session.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw LLMError.invalidResponse
            }
            
            if httpResponse.statusCode != 200 {
                let errorMessage = String(data: data, encoding: .utf8) ?? "Unknown error"
                throw LLMError.apiError("HTTP \(httpResponse.statusCode): \(errorMessage)")
            }
            
            let llmResponse = try JSONDecoder().decode(LLMResponse.self, from: data)
            
            guard let firstChoice = llmResponse.choices.first else {
                throw LLMError.invalidResponse
            }
            
            return firstChoice.message.content
        } catch let error as LLMError {
            throw error
        } catch {
            throw LLMError.networkError(error)
        }
    }
}
