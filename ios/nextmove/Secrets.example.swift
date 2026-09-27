//
//  Secrets.example.swift
//  nextmove
//
//  TEMPLATE — copy this file to `Secrets.swift` (same folder) and fill in your
//  own key, then rename the enum from `SecretsExample` to `Secrets`.
//
//      cp Secrets.example.swift Secrets.swift
//      # then in Secrets.swift : SecretsExample -> Secrets, and set groqAPIKey
//
//  `Secrets.swift` is gitignored on purpose so real keys never land in git.
//  Without it, the AI Coach falls back to the on-device rule-based coach.
//
//  NOTE: the type here is `SecretsExample` (not `Secrets`) so this template can
//  live in the repo alongside your real `Secrets.swift` without a name clash.
//  Get a Groq key at https://console.groq.com — rotate it if ever exposed.
//

import Foundation

enum SecretsExample {
    /// Groq API key (OpenAI-compatible). Empty => AI Coach uses the rule-based fallback.
    static let groqAPIKey = ""

    /// Groq's OpenAI-compatible endpoint.
    static let groqBaseURL = "https://api.groq.com/openai/v1"

    /// A model available on your Groq account.
    static let groqModel = "openai/gpt-oss-20b"
}
