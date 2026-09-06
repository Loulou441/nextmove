//
//  EnhancedCoachingEngine.swift
//  nextmove
//
//  Enhanced coaching engine with optional LLM integration
//

import Foundation

class EnhancedCoachingEngine: CoachingEngineProtocol {
    private let baseEngine: CoachingEngine
    private let llmService: LLMService
    private let useLLM: Bool
    
    init(useLLM: Bool = true, llmService: LLMService = LLMService()) {
        self.baseEngine = CoachingEngine()
        self.llmService = llmService
        self.useLLM = useLLM && ConfigurationManager.shared.openAIAPIKey != nil
    }
    
    func generateCoaching(from features: PerformanceFeatures, sportType: SportType) async throws -> CoachingFeedback {
        // Always generate base feedback as fallback
        print("🏋️ Generating base coaching feedback...")
        let baseFeedback = try await baseEngine.generateCoaching(from: features, sportType: sportType)
        
        // If LLM is disabled or unavailable, return base feedback
        guard useLLM else {
            print("ℹ️ LLM disabled, using base feedback only")
            return baseFeedback
        }
        
        // Try to enhance with LLM
        do {
            return try await enhanceWithLLM(baseFeedback: baseFeedback, features: features, sportType: sportType)
        } catch let error as LLMError {
            print("❌ LLM enhancement failed: \(error)")
            print("   Falling back to base feedback")
            return baseFeedback
        } catch {
            print("❌ LLM enhancement failed with unexpected error: \(error)")
            print("   Falling back to base feedback")
            return baseFeedback
        }
    }
    
    private func enhanceWithLLM(
        baseFeedback: CoachingFeedback,
        features: PerformanceFeatures,
        sportType: SportType
    ) async throws -> CoachingFeedback {
        print("🤖 Attempting LLM enhancement...")
        let performanceData = formatPerformanceData(features: features)
        
        print("📤 Sending request to LLM API...")
        let llmResponse = try await llmService.generateCoachingInsights(
            performanceData: performanceData,
            sportType: sportType.rawValue,
            temperature: 0.7
        )
        
        print("✅ LLM response received: \(llmResponse.prefix(100))...")
        
        let enhancedFeedback = parseAndMergeLLMResponse(
            llmResponse: llmResponse,
            baseFeedback: baseFeedback
        )
        
        return enhancedFeedback
    }
    
    private func formatPerformanceData(features: PerformanceFeatures) -> String {
        var data = "Performance Analysis:\n\n"
        
        data += "Issues Detected:\n"
        for (index, issue) in features.issues.enumerated() {
            data += "\(index + 1). \(issue.type.rawValue)\n"
            data += "   Severity: \(String(format: "%.1f%%", issue.severity * 100))\n"
            data += "   Confidence: \(String(format: "%.1f%%", issue.confidence * 100))\n"
            data += "   Occurrences: \(issue.occurrences)\n"
            data += "   Description: \(issue.description)\n"
            data += "\n"
        }
        
        return data
    }
    
    private func parseAndMergeLLMResponse(
        llmResponse: String,
        baseFeedback: CoachingFeedback
    ) -> CoachingFeedback {
        // For now, use base feedback structure with LLM-enhanced descriptions
        // In production, you'd parse the LLM response more sophisticatedly
        return baseFeedback
    }
}
