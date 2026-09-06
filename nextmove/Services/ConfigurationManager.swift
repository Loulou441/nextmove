//
//  ConfigurationManager.swift
//  nextmove
//
//  Manages environment configuration and API keys
//

import Foundation

class ConfigurationManager {
    static let shared = ConfigurationManager()
    
    private var config: [String: String] = [:]
    
    private init() {
        loadConfiguration()
    }
    
    private func loadConfiguration() {
        // Try to load from .env file
        if let envPath = Bundle.main.path(forResource: ".env", ofType: nil) {
            loadFromFile(path: envPath)
        }
        
        // Override with Info.plist values if present
        loadFromInfoPlist()
        
        // Override with environment variables (for development)
        loadFromEnvironment()
    }
    
    private func loadFromFile(path: String) {
        guard let contents = try? String(contentsOfFile: path, encoding: .utf8) else {
            return
        }
        
        let lines = contents.components(separatedBy: .newlines)
        for line in lines {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            
            // Skip comments and empty lines
            if trimmed.isEmpty || trimmed.hasPrefix("#") {
                continue
            }
            
            // Parse KEY=VALUE
            let parts = trimmed.components(separatedBy: "=")
            if parts.count >= 2 {
                let key = parts[0].trimmingCharacters(in: .whitespaces)
                let value = parts[1...].joined(separator: "=").trimmingCharacters(in: .whitespaces)
                config[key] = value
            }
        }
    }
    
    private func loadFromInfoPlist() {
        if let infoPlist = Bundle.main.infoDictionary {
            for (key, value) in infoPlist {
                if let stringValue = value as? String {
                    config[key] = stringValue
                }
            }
        }
    }
    
    private func loadFromEnvironment() {
        let envKeys = ["OPENAI_API_KEY", "OPENAI_API_BASE_URL", "OPENAI_MODEL", "OPENAI_ORG_ID"]
        for key in envKeys {
            if let value = ProcessInfo.processInfo.environment[key] {
                config[key] = value
            }
        }
    }
    
    func get(_ key: String) -> String? {
        return config[key]
    }
    
    func get(_ key: String, default defaultValue: String) -> String {
        return config[key] ?? defaultValue
    }
    
    var openAIAPIKey: String? {
        return get("OPENAI_API_KEY")
    }
    
    var openAIBaseURL: String {
        return get("OPENAI_API_BASE_URL", default: "https://api.openai.com/v1")
    }
    
    var openAIModel: String {
        return get("OPENAI_MODEL", default: "gpt-4o-mini")
    }
    
    var openAIOrgID: String? {
        return get("OPENAI_ORG_ID")
    }
}
