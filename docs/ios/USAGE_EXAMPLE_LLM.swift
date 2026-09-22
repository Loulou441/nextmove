//
//  USAGE_EXAMPLE_LLM.swift
//  Example of using LLM-enhanced coaching in nextmove
//

import Foundation

// MARK: - Example 1: Using Enhanced Coaching in ViewModel

class ExampleRecordingViewModel {
    
    func analyzeRecordingWithLLM(recording: GameRecording) async throws {
        // Initialize components
        let modelManager = ModelManager()
        let videoProcessor = VideoProcessor()
        let objectDetector = ObjectDetector(modelManager: modelManager)
        let objectTracker = ObjectTracker()
        let featureExtractor = FeatureExtractor()
        
        // Create pipeline with LLM-enhanced coaching
        let pipeline = AnalysisPipeline.withLLMCoaching(
            videoProcessor: videoProcessor,
            objectDetector: objectDetector,
            objectTracker: objectTracker,
            featureExtractor: featureExtractor,
            modelManager: modelManager,
            useLLM: true  // Enable LLM enhancement
        )
        
        // Monitor progress
        Task {
            for await progress in pipeline.progress {
                print("Progress: \(progress.stage) - \(progress.percentage * 100)%")
                print("Message: \(progress.message)")
            }
        }
        
        // Run analysis
        let analysis = try await pipeline.analyze(
            recording: recording,
            sportType: .pickleball
        )
        
        print("Analysis complete!")
        print("Overall rating: \(analysis.overallRating)")
    }
}

// MARK: - Example 2: Direct LLM Service Usage

class ExampleDirectLLMUsage {
    
    func generateCustomCoaching() async throws {
        let llmService = LLMService()
        
        let performanceData = """
        Player showed:
        - 80% time spent in optimal position
        - 15% late contact timing on backhand
        - Good court coverage (85%)
        """
        
        let insights = try await llmService.generateCoachingInsights(
            performanceData: performanceData,
            sportType: "pickleball",
            temperature: 0.7
        )
        
        print("LLM Coaching Insights:")
        print(insights)
    }
    
    func enhanceSpecificDescription() async throws {
        let llmService = LLMService()
        
        let description = try await llmService.enhanceCoachingDescription(
            issueType: "Late Contact Timing",
            metrics: "15% of shots on backhand side",
            confidence: 0.85,
            sportType: "pickleball"
        )
        
        print("Enhanced Description:")
        print(description)
    }
}

// MARK: - Example 3: Configuration Check

class ExampleConfigurationCheck {
    
    func checkLLMConfiguration() {
        let config = ConfigurationManager.shared
        
        if let apiKey = config.openAIAPIKey {
            print("✅ API Key configured")
            print("Base URL: \(config.openAIBaseURL)")
            print("Model: \(config.openAIModel)")
            
            if let orgID = config.openAIOrgID {
                print("Organization ID: \(orgID)")
            }
        } else {
            print("⚠️ No API key configured - will use rule-based coaching")
        }
    }
}

// MARK: - Example 4: Fallback Behavior

class ExampleFallbackBehavior {
    
    func demonstrateFallback() async throws {
        let modelManager = ModelManager()
        let videoProcessor = VideoProcessor()
        let objectDetector = ObjectDetector(modelManager: modelManager)
        let objectTracker = ObjectTracker()
        let featureExtractor = FeatureExtractor()
        
        // Even without API key, this will work using base coaching
        let pipeline = AnalysisPipeline.withLLMCoaching(
            videoProcessor: videoProcessor,
            objectDetector: objectDetector,
            objectTracker: objectTracker,
            featureExtractor: featureExtractor,
            modelManager: modelManager,
            useLLM: true  // Will automatically fall back if no API key
        )
        
        // Analysis will complete successfully with rule-based coaching
        // No errors or crashes
    }
}

// MARK: - Example 5: Switching Between Modes

class ExampleModeSwitching {
    
    func analyzeWithDifferentModes(recording: GameRecording) async throws {
        let modelManager = ModelManager()
        let videoProcessor = VideoProcessor()
        let objectDetector = ObjectDetector(modelManager: modelManager)
        let objectTracker = ObjectTracker()
        let featureExtractor = FeatureExtractor()
        
        // Mode 1: LLM-enhanced
        let llmPipeline = AnalysisPipeline.withLLMCoaching(
            videoProcessor: videoProcessor,
            objectDetector: objectDetector,
            objectTracker: objectTracker,
            featureExtractor: featureExtractor,
            modelManager: modelManager,
            useLLM: true
        )
        
        // Mode 2: Standard rule-based
        let standardPipeline = AnalysisPipeline.withStandardCoaching(
            videoProcessor: videoProcessor,
            objectDetector: objectDetector,
            objectTracker: objectTracker,
            featureExtractor: featureExtractor,
            modelManager: modelManager
        )
        
        // Use based on user preference or settings
        let useEnhanced = UserDefaults.standard.bool(forKey: "useLLMCoaching")
        let pipeline = useEnhanced ? llmPipeline : standardPipeline
        
        let analysis = try await pipeline.analyze(
            recording: recording,
            sportType: .pickleball
        )
    }
}
