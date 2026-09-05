//
//  ModelManager.swift
//  nextmove
//
//  Manages Core ML model loading, caching, and lifecycle
//  Validates: Requirements 13.1-13.8, 28.1-28.7
//

import Foundation
import CoreML
import UIKit
import os.log

/// Manages Core ML model loading, caching, and memory lifecycle
/// Validates: Requirements 13.1-13.8, 28.1-28.7
final class ModelManager: ModelManagerProtocol {
    
    // MARK: - Properties
    
    /// Cache of loaded models keyed by sport type and version
    private var modelCache: [String: MLModel] = [:]
    
    /// Lock for thread-safe cache access
    private let cacheLock = NSLock()
    
    /// Logger for debugging and observability
    private let logger = Logger(subsystem: "com.nextmove.cvml", category: "ModelManager")
    
    /// Notification observer for memory warnings
    private var memoryWarningObserver: NSObjectProtocol?
    
    // MARK: - Initialization
    
    init() {
        setupMemoryWarningObserver()
    }
    
    deinit {
        if let observer = memoryWarningObserver {
            NotificationCenter.default.removeObserver(observer)
        }
    }
    
    // MARK: - ModelManagerProtocol Implementation
    
    /// Loads a Core ML model for the specified sport and version
    /// Validates: Requirements 13.1, 13.2, 13.4, 13.5, 13.6, 13.7, 28.1, 28.2, 28.3, 28.6
    /// - Parameters:
    ///   - sportType: Sport type to load model for
    ///   - version: Optional model version (defaults to latest if nil)
    /// - Returns: Loaded MLModel instance
    /// - Throws: ModelLoadingError if loading fails
    func loadModel(for sportType: SportType, version: String? = nil) async throws -> MLModel {
        let cacheKey = makeCacheKey(sportType: sportType, version: version)
        
        // Check cache first (Requirement 13.7)
        cacheLock.lock()
        if let cachedModel = modelCache[cacheKey] {
            cacheLock.unlock()
            logger.info("Loaded model from cache: \(cacheKey)")
            return cachedModel
        }
        cacheLock.unlock()
        
        // Load model from bundle
        let startTime = CFAbsoluteTimeGetCurrent()
        
        do {
            let model = try await loadModelFromBundle(sportType: sportType, version: version)
            
            // Validate model compatibility (Requirement 13.2)
            try validateModelCompatibility(model)
            
            // Cache the loaded model (Requirement 13.7)
            cacheLock.lock()
            modelCache[cacheKey] = model
            cacheLock.unlock()
            
            let loadTime = CFAbsoluteTimeGetCurrent() - startTime
            logger.info("Loaded model \(cacheKey) in \(String(format: "%.3f", loadTime))s")
            
            return model
            
        } catch let error as ModelLoadingError {
            logger.error("Failed to load model \(cacheKey): \(error.localizedDescription)")
            throw error
        } catch {
            logger.error("Unexpected error loading model \(cacheKey): \(error.localizedDescription)")
            throw ModelLoadingError.compilationFailed(reason: error.localizedDescription)
        }
    }
    
    /// Releases cached models to free memory
    /// Validates: Requirements 13.8
    func releaseModels() {
        cacheLock.lock()
        let count = modelCache.count
        modelCache.removeAll()
        cacheLock.unlock()
        
        logger.info("Released \(count) cached model(s)")
    }
    
    // MARK: - Private Methods
    
    /// Loads a model from the app bundle
    /// Validates: Requirements 13.1, 13.4, 28.1, 28.2, 28.3
    private func loadModelFromBundle(sportType: SportType, version: String?) async throws -> MLModel {
        // Determine model name and path
        let modelName = makeModelName(sportType: sportType, version: version)
        let modelDirectory = makeModelDirectory(sportType: sportType)
        
        logger.info("🔍 Looking for model: \(modelName)")
        logger.info("   Directory: \(modelDirectory)")
        
        // Try .mlpackage first (uncompiled)
        if let packagePath = Bundle.main.path(forResource: modelName, ofType: "mlpackage", inDirectory: modelDirectory) {
            logger.info("✅ Found .mlpackage at: \(packagePath)")
            return try await loadModelAtPath(packagePath)
        }
        
        // Try .mlmodelc (compiled)
        if let compiledPath = Bundle.main.path(forResource: modelName, ofType: "mlmodelc", inDirectory: modelDirectory) {
            logger.info("✅ Found .mlmodelc at: \(compiledPath)")
            return try await loadModelAtPath(compiledPath)
        }
        
        // Try without directory for backward compatibility
        if let packagePath = Bundle.main.path(forResource: modelName, ofType: "mlpackage") {
            logger.info("✅ Found .mlpackage (no directory) at: \(packagePath)")
            return try await loadModelAtPath(packagePath)
        }
        
        if let compiledPath = Bundle.main.path(forResource: modelName, ofType: "mlmodelc") {
            logger.info("✅ Found .mlmodelc (no directory) at: \(compiledPath)")
            return try await loadModelAtPath(compiledPath)
        }
        
        // Last resort: recursively scan the whole bundle for a matching model file.
        // Synchronized folder groups (Xcode 16+) can place resources at unexpected paths.
        if let resourcePath = Bundle.main.resourcePath {
            let fileManager = FileManager.default
            if let enumerator = fileManager.enumerator(atPath: resourcePath) {
                var availableModels: [String] = []
                for case let file as String in enumerator {
                    let isCompiled = file.hasSuffix(".mlmodelc")
                    let isPackage = file.hasSuffix(".mlpackage")
                    guard isCompiled || isPackage else { continue }
                    availableModels.append(file)

                    // Match by base name (e.g. "PickleballDetector_v1")
                    let base = (file as NSString).lastPathComponent
                    if base == "\(modelName).mlmodelc" || base == "\(modelName).mlpackage" {
                        let fullPath = (resourcePath as NSString).appendingPathComponent(file)
                        logger.info("✅ Found model via recursive scan: \(fullPath)")
                        return try await loadModelAtPath(fullPath)
                    }
                }
                logger.error("❌ Model not found: \(modelName) (searched \(modelDirectory))")
                logger.error("   Available ML models in bundle: \(availableModels.isEmpty ? "NONE" : availableModels.joined(separator: ", "))")
            }
        }

        throw ModelLoadingError.modelNotFound(sportType: sportType, version: version)
    }
    
    /// Loads a model from a specific file path
    /// Validates: Requirements 13.1, 13.3
    private func loadModelAtPath(_ path: String) async throws -> MLModel {
        let modelURL = URL(fileURLWithPath: path)

        let configuration = MLModelConfiguration()
        configuration.computeUnits = .all // CPU, GPU, Neural Engine

        do {
            // A folder that contains a Manifest.json is an .mlpackage (or an
            // .mlmodelc that is actually a package). MLModel can load these
            // directly — calling compileModel on them fails with
            // "A valid manifest does not exist".
            let manifestURL = modelURL.appendingPathComponent("Manifest.json")
            let isPackage = FileManager.default.fileExists(atPath: manifestURL.path)

            if isPackage {
                logger.info("Loading model as package/compiled directly: \(modelURL.lastPathComponent)")
                return try MLModel(contentsOf: modelURL, configuration: configuration)
            }

            // Otherwise treat it as a source model that needs compilation
            // (e.g. a raw .mlmodel), then load the compiled result.
            logger.info("Compiling model: \(modelURL.lastPathComponent)")
            let compiledURL = try await MLModel.compileModel(at: modelURL)
            return try MLModel(contentsOf: compiledURL, configuration: configuration)

        } catch let error as NSError {
            // If a direct load failed, try the opposite approach as a fallback.
            if let fallback = try? await recoverLoad(modelURL, configuration: configuration) {
                return fallback
            }
            if error.domain == NSCocoaErrorDomain && error.code == NSFileReadNoSuchFileError {
                throw ModelLoadingError.modelNotFound(sportType: .pickleball, version: nil)
            } else if error.localizedDescription.contains("memory") {
                throw ModelLoadingError.memoryAllocationFailed
            } else {
                throw ModelLoadingError.compilationFailed(reason: error.localizedDescription)
            }
        }
    }

    /// Best-effort recovery: try both direct load and compile-then-load.
    private func recoverLoad(_ url: URL, configuration: MLModelConfiguration) async throws -> MLModel? {
        if let direct = try? MLModel(contentsOf: url, configuration: configuration) {
            return direct
        }
        if let compiledURL = try? await MLModel.compileModel(at: url),
           let compiled = try? MLModel(contentsOf: compiledURL, configuration: configuration) {
            return compiled
        }
        return nil
    }
    
    /// Validates that the model is compatible with the current iOS version
    /// Validates: Requirements 13.2, 28.6
    private func validateModelCompatibility(_ model: MLModel) throws {
        let modelDescription = model.modelDescription
        
        // Check if model metadata contains minimum iOS version requirement
        if let metadata = modelDescription.metadata[.creatorDefinedKey] as? [String: String],
           let requiredVersion = metadata["minimumIOSVersion"] {
            
            let currentVersion = ProcessInfo.processInfo.operatingSystemVersion
            let currentVersionString = "\(currentVersion.majorVersion).\(currentVersion.minorVersion)"
            
            // Simple version comparison (major.minor)
            if !isVersionCompatible(current: currentVersionString, required: requiredVersion) {
                throw ModelLoadingError.incompatibleVersion(
                    required: requiredVersion,
                    current: currentVersionString
                )
            }
        }
        
        // Model loaded successfully and is compatible
        logger.debug("Model validation passed")
    }
    
    /// Compares version strings for compatibility
    private func isVersionCompatible(current: String, required: String) -> Bool {
        let currentComponents = current.split(separator: ".").compactMap { Int($0) }
        let requiredComponents = required.split(separator: ".").compactMap { Int($0) }
        
        guard currentComponents.count >= 2, requiredComponents.count >= 2 else {
            return true // If we can't parse, assume compatible
        }
        
        // Compare major version
        if currentComponents[0] > requiredComponents[0] {
            return true
        } else if currentComponents[0] < requiredComponents[0] {
            return false
        }
        
        // Major versions equal, compare minor version
        return currentComponents[1] >= requiredComponents[1]
    }
    
    /// Creates a cache key for a model
    private func makeCacheKey(sportType: SportType, version: String?) -> String {
        if let version = version {
            return "\(sportType.rawValue)_\(version)"
        } else {
            return "\(sportType.rawValue)_latest"
        }
    }
    
    /// Creates the model name based on sport type and version
    /// Validates: Requirements 13.4, 28.1
    private func makeModelName(sportType: SportType, version: String?) -> String {
        let baseName: String
        switch sportType {
        case .pickleball:
            baseName = "PickleballDetector"
        case .padel:
            // Dedicated padel model (Plaimaker padel-tkrqs, Roboflow Universe).
            baseName = "PadelDetector"
        case .tennis, .badminton:
            // Badminton reuses the tennis detector as a transfer stand-in
            // (fast small projectile, net-divided court — closest trained match).
            baseName = "TennisDetector"
        }
        
        if let version = version {
            return "\(baseName)_\(version)"
        } else {
            // Default to v1 if no version specified
            return "\(baseName)_v1"
        }
    }
    
    /// Creates the model directory path based on sport type
    /// Validates: Requirements 13.1
    private func makeModelDirectory(sportType: SportType) -> String {
        switch sportType {
        case .pickleball:
            return "Models/Pickleball"
        case .padel:
            // Dedicated padel model (Plaimaker padel-tkrqs, Roboflow Universe).
            return "Models/Padel"
        case .tennis, .badminton:
            // Badminton reuses the tennis detector (transfer stand-in).
            return "Models/Tennis"
        }
    }
    
    /// Sets up observer for memory warnings to release cached models
    /// Validates: Requirements 13.8
    private func setupMemoryWarningObserver() {
        memoryWarningObserver = NotificationCenter.default.addObserver(
            forName: UIApplication.didReceiveMemoryWarningNotification,
            object: nil,
            queue: .main
        ) { [weak self] _ in
            self?.handleMemoryWarning()
        }
    }
    
    /// Handles memory warning by releasing cached models
    /// Validates: Requirements 13.8
    private func handleMemoryWarning() {
        logger.warning("Memory warning received, releasing cached models")
        releaseModels()
    }
}

// MARK: - Model Versioning Support

extension ModelManager {
    
    /// Attempts to load a model with fallback to previous version
    /// Validates: Requirements 28.3, 28.4
    func loadModelWithFallback(for sportType: SportType, preferredVersion: String) async throws -> MLModel {
        do {
            // Try to load preferred version
            return try await loadModel(for: sportType, version: preferredVersion)
        } catch {
            logger.warning("Failed to load \(sportType.rawValue) v\(preferredVersion), falling back to default version")
            
            // Fall back to default version (v1)
            return try await loadModel(for: sportType, version: nil)
        }
    }
    
    /// Returns the version of a loaded model from cache
    /// Validates: Requirements 28.4
    func getCachedModelVersion(for sportType: SportType) -> String? {
        cacheLock.lock()
        defer { cacheLock.unlock() }
        
        // Check if any version of this sport's model is cached
        for key in modelCache.keys {
            if key.hasPrefix(sportType.rawValue) {
                let components = key.split(separator: "_")
                if components.count > 1 {
                    return String(components[1])
                }
            }
        }
        
        return nil
    }
}
