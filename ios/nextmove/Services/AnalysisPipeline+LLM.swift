//
//  AnalysisPipeline+LLM.swift
//  nextmove
//
//  Extension to create AnalysisPipeline with LLM-enhanced coaching
//

import Foundation

extension AnalysisPipeline {
    
    /// Creates an AnalysisPipeline with LLM-enhanced coaching engine
    /// Falls back to base coaching if API key is not configured
    static func withLLMCoaching(
        videoProcessor: VideoProcessorProtocol,
        objectDetector: ObjectDetectorProtocol,
        objectTracker: ObjectTrackerProtocol,
        featureExtractor: FeatureExtractorProtocol,
        modelManager: ModelManagerProtocol,
        useLLM: Bool = true
    ) -> AnalysisPipeline {
        let coachingEngine: CoachingEngineProtocol = EnhancedCoachingEngine(useLLM: useLLM)
        
        return AnalysisPipeline(
            videoProcessor: videoProcessor,
            objectDetector: objectDetector,
            objectTracker: objectTracker,
            featureExtractor: featureExtractor,
            coachingEngine: coachingEngine,
            modelManager: modelManager
        )
    }
    
    /// Creates a standard AnalysisPipeline with rule-based coaching
    static func withStandardCoaching(
        videoProcessor: VideoProcessorProtocol,
        objectDetector: ObjectDetectorProtocol,
        objectTracker: ObjectTrackerProtocol,
        featureExtractor: FeatureExtractorProtocol,
        modelManager: ModelManagerProtocol
    ) -> AnalysisPipeline {
        let coachingEngine: CoachingEngineProtocol = CoachingEngine()
        
        return AnalysisPipeline(
            videoProcessor: videoProcessor,
            objectDetector: objectDetector,
            objectTracker: objectTracker,
            featureExtractor: featureExtractor,
            coachingEngine: coachingEngine,
            modelManager: modelManager
        )
    }
}
