//
//  LLMIntegrationGuide.swift
//  nextmove
//
//  Step-by-step guide for integrating LLM into your existing code
//

import Foundation

/*
 
 STEP 1: FIND YOUR EXISTING PIPELINE INITIALIZATION
 ===================================================
 
 Look for code that creates an AnalysisPipeline. It might be in:
 - RecordingViewModel.swift
 - A service class
 - Your main analysis coordinator
 
 Current code probably looks like:
 
 ```swift
 let videoProcessor = VideoProcessor()
 let modelManager = ModelManager()
 let objectDetector = ObjectDetector(modelManager: modelManager)
 let objectTracker = ObjectTracker()
 let featureExtractor = FeatureExtractor()
 let coachingEngine = CoachingEngine()  // ← This line changes
 
 let pipeline = AnalysisPipeline(
     videoProcessor: videoProcessor,
     objectDetector: objectDetector,
     objectTracker: objectTracker,
     featureExtractor: featureExtractor,
     coachingEngine: coachingEngine,  // ← This parameter changes
     modelManager: modelManager
 )
 ```
 
 
 STEP 2: REPLACE WITH LLM-ENHANCED VERSION
 ==========================================
 
 Option A: Use factory method (RECOMMENDED)
 ```swift
 let videoProcessor = VideoProcessor()
 let modelManager = ModelManager()
 let objectDetector = ObjectDetector(modelManager: modelManager)
 let objectTracker = ObjectTracker()
 let featureExtractor = FeatureExtractor()
 
 // Use factory method - automatically handles LLM availability
 let pipeline = AnalysisPipeline.withLLMCoaching(
     videoProcessor: videoProcessor,
     objectDetector: objectDetector,
     objectTracker: objectTracker,
     featureExtractor: featureExtractor,
     modelManager: modelManager,
     useLLM: true  // Set to false to disable LLM
 )
 ```
 
 Option B: Manual initialization
 ```swift
 let videoProcessor = VideoProcessor()
 let modelManager = ModelManager()
 let objectDetector = ObjectDetector(modelManager: modelManager)
 let objectTracker = ObjectTracker()
 let featureExtractor = FeatureExtractor()
 
 // Create enhanced coaching engine
 let coachingEngine = EnhancedCoachingEngine(useLLM: true)
 
 let pipeline = AnalysisPipeline(
     videoProcessor: videoProcessor,
     objectDetector: objectDetector,
     objectTracker: objectTracker,
     featureExtractor: featureExtractor,
     coachingEngine: coachingEngine,
     modelManager: modelManager
 )
 ```
 
 
 STEP 3: ADD CONFIGURATION CHECK (OPTIONAL)
 ===========================================
 
 Add this to help debug configuration issues:
 
 ```swift
 func checkLLMConfiguration() {
     let config = ConfigurationManager.shared
     
     if let _ = config.openAIAPIKey {
         print("✅ LLM enabled")
         print("   Model: \(config.openAIModel)")
         print("   Endpoint: \(config.openAIBaseURL)")
     } else {
         print("ℹ️ LLM not configured - using rule-based coaching")
     }
 }
 
 // Call before analysis
 checkLLMConfiguration()
 ```
 
 
 STEP 4: ADD USER PREFERENCE (OPTIONAL)
 =======================================
 
 Let users toggle LLM on/off:
 
 ```swift
 // In your settings or preferences
 @AppStorage("enableLLMCoaching") private var enableLLM = true
 
 // When creating pipeline
 let pipeline = AnalysisPipeline.withLLMCoaching(
     videoProcessor: videoProcessor,
     objectDetector: objectDetector,
     objectTracker: objectTracker,
     featureExtractor: featureExtractor,
     modelManager: modelManager,
     useLLM: enableLLM
 )
 ```
 
 
 STEP 5: HANDLE ERRORS (OPTIONAL)
 =================================
 
 LLM errors are handled automatically, but you can add custom handling:
 
 ```swift
 do {
     let analysis = try await pipeline.analyze(
         recording: recording,
         sportType: .pickleball
     )
     
     // Success - analysis includes coaching feedback
     print("Analysis complete with \(analysis.insights.count) insights")
     
 } catch let error as LLMError {
     // LLM-specific error (rare - usually falls back automatically)
     print("LLM error: \(error)")
     // Analysis still completes with base coaching
     
 } catch {
     // Other analysis errors
     print("Analysis failed: \(error)")
 }
 ```
 
 
 COMPLETE EXAMPLE: RecordingViewModel
 =====================================
 
 Here's a complete example of integrating into a ViewModel:
 
 ```swift
 import SwiftUI
 
 @MainActor
 class RecordingViewModel: ObservableObject {
     @Published var isAnalyzing = false
     @Published var analysisProgress: Double = 0.0
     @Published var currentAnalysis: GameAnalysis?
     
     @AppStorage("enableLLMCoaching") private var enableLLM = true
     
     private var pipeline: AnalysisPipeline?
     
     init() {
         setupPipeline()
     }
     
     private func setupPipeline() {
         let videoProcessor = VideoProcessor()
         let modelManager = ModelManager()
         let objectDetector = ObjectDetector(modelManager: modelManager)
         let objectTracker = ObjectTracker()
         let featureExtractor = FeatureExtractor()
         
         // Use LLM-enhanced pipeline
         pipeline = AnalysisPipeline.withLLMCoaching(
             videoProcessor: videoProcessor,
             objectDetector: objectDetector,
             objectTracker: objectTracker,
             featureExtractor: featureExtractor,
             modelManager: modelManager,
             useLLM: enableLLM
         )
         
         // Log configuration
         logConfiguration()
     }
     
     private func logConfiguration() {
         let config = ConfigurationManager.shared
         if config.openAIAPIKey != nil {
             print("✅ LLM coaching enabled (\(config.openAIModel))")
         } else {
             print("ℹ️ Using rule-based coaching")
         }
     }
     
     func analyzeRecording(_ recording: GameRecording) async {
         guard let pipeline = pipeline else { return }
         
         isAnalyzing = true
         analysisProgress = 0.0
         
         // Monitor progress
         Task {
             for await progress in pipeline.progress {
                 analysisProgress = progress.percentage
             }
         }
         
         do {
             let analysis = try await pipeline.analyze(
                 recording: recording,
                 sportType: .pickleball
             )
             
             currentAnalysis = analysis
             print("✅ Analysis complete!")
             
         } catch {
             print("❌ Analysis failed: \(error)")
         }
         
         isAnalyzing = false
     }
     
     func toggleLLM() {
         enableLLM.toggle()
         setupPipeline() // Recreate pipeline with new setting
     }
 }
 ```
 
 
 TESTING YOUR INTEGRATION
 =========================
 
 1. Build the project (⌘B)
 2. Run on simulator/device
 3. Check console for configuration message
 4. Analyze a video
 5. Verify coaching feedback is generated
 
 Expected console output:
 ```
 ✅ LLM coaching enabled (gpt-4o-mini)
 Starting analysis for recording...
 Progress: frameExtraction - 20.0%
 Progress: objectDetection - 50.0%
 Progress: objectTracking - 65.0%
 Progress: featureExtraction - 80.0%
 Progress: coachingGeneration - 95.0%
 ✅ Analysis complete!
 ```
 
 
 TROUBLESHOOTING
 ===============
 
 Problem: "Cannot find 'EnhancedCoachingEngine' in scope"
 Solution: Add EnhancedCoachingEngine.swift to Xcode target
 
 Problem: "API Key not configured" but I added it
 Solution: Restart Xcode, verify .env is in project target
 
 Problem: Analysis takes too long
 Solution: LLM adds 1-3 seconds. Use gpt-4o-mini for speed
 
 Problem: Coaching feedback seems generic
 Solution: This is expected - LLM enhances but doesn't replace base logic
 
 
 NEXT STEPS
 ==========
 
 1. ✅ Integrate into your code (follow steps above)
 2. ✅ Test with real videos
 3. ✅ Monitor API costs in OpenAI dashboard
 4. ✅ Adjust model/temperature based on results
 5. ✅ Add user preference toggle (optional)
 
 */

// MARK: - Helper Extensions

extension AnalysisPipeline {
    /// Convenience method to check if LLM is available
    static func isLLMAvailable() -> Bool {
        return ConfigurationManager.shared.openAIAPIKey != nil
    }
}

// MARK: - Example Usage in SwiftUI View

/*
 
 struct AnalysisView: View {
     @StateObject private var viewModel = RecordingViewModel()
     
     var body: some View {
         VStack {
             if viewModel.isAnalyzing {
                 ProgressView(value: viewModel.analysisProgress) {
                     Text("Analyzing...")
                 }
             }
             
             if let analysis = viewModel.currentAnalysis {
                 Text("Overall Rating: \(analysis.overallRating, specifier: "%.1f")")
                 
                 ForEach(analysis.insights) { insight in
                     InsightCard(insight: insight)
                 }
             }
             
             Button("Analyze Video") {
                 Task {
                     await viewModel.analyzeRecording(selectedRecording)
                 }
             }
             
             Toggle("Use AI Coaching", isOn: $viewModel.enableLLM)
                 .onChange(of: viewModel.enableLLM) { _ in
                     viewModel.toggleLLM()
                 }
         }
     }
 }
 
 */
