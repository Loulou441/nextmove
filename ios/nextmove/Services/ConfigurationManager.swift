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
        // 0) Compiled-in secrets (most reliable: always in the app since it's a
        //    Swift source, not a bundled resource file). Only applied when set.
        if !Secrets.groqAPIKey.isEmpty {
            config["GROQ_API_KEY"] = Secrets.groqAPIKey
            config["GROQ_API_BASE_URL"] = Secrets.groqBaseURL
            config["GROQ_MODEL"] = Secrets.groqModel
        }

        // 1) Bundled .env (works when the file is copied into the app bundle).
        if let envPath = Bundle.main.path(forResource: ".env", ofType: nil) {
            loadFromFile(path: envPath)
        }
        // Some build setups also copy it named "env" (no dot) or "env.txt".
        if let envPath = Bundle.main.path(forResource: "env", ofType: nil) {
            loadFromFile(path: envPath)
        }
        if let envPath = Bundle.main.path(forResource: "env", ofType: "txt") {
            loadFromFile(path: envPath)
        }

        // 2) Bundled Secrets.plist — the RELIABLE delivery for a synchronized Xcode
        //    project (hidden dotfiles are often skipped by the build; a .plist is not).
        loadFromPlist(named: "Secrets")

        // 3) Info.plist values, if present.
        loadFromInfoPlist()

        // 4) Environment variables (for development / scheme env).
        loadFromEnvironment()
    }

    /// Loads KEY→value pairs from a bundled property list (e.g. Secrets.plist).
    private func loadFromPlist(named name: String) {
        guard let url = Bundle.main.url(forResource: name, withExtension: "plist"),
              let dict = NSDictionary(contentsOf: url) as? [String: Any] else {
            return
        }
        for (key, value) in dict {
            if let stringValue = value as? String, !stringValue.isEmpty {
                config[key] = stringValue
            }
        }
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
                if !value.isEmpty { config[key] = value }  // don't overwrite with empty
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
        let envKeys = [
            "OPENAI_API_KEY", "OPENAI_API_BASE_URL", "OPENAI_MODEL", "OPENAI_ORG_ID",
            "GROQ_API_KEY", "GROQ_API_BASE_URL", "GROQ_MODEL"
        ]
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
    
    // The AI Coach uses an OpenAI-compatible client. Groq is OpenAI-compatible,
    // so GROQ_* keys are accepted as aliases and take precedence when present.
    var openAIAPIKey: String? {
        return get("GROQ_API_KEY") ?? get("OPENAI_API_KEY")
    }
    
    var openAIBaseURL: String {
        if let groqBase = get("GROQ_API_BASE_URL") { return groqBase }
        // If a Groq key is configured but no explicit base URL, default to Groq's endpoint.
        if get("GROQ_API_KEY") != nil { return get("OPENAI_API_BASE_URL", default: "https://api.groq.com/openai/v1") }
        return get("OPENAI_API_BASE_URL", default: "https://api.openai.com/v1")
    }
    
    var openAIModel: String {
        if let groqModel = get("GROQ_MODEL") { return groqModel }
        return get("OPENAI_MODEL", default: "gpt-4o-mini")
    }
    
    var openAIOrgID: String? {
        return get("OPENAI_ORG_ID")
    }
}
