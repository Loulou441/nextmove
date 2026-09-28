//
//  LanguageManager.swift
//  nextmove
//
//  App-wide language selection. Mirrors SportManager: a persisted @AppStorage
//  value backing a @Published enum, injected as an @EnvironmentObject so every
//  view can read it and the coaching layer can localize AI output.
//
//  How the UI language switch actually takes effect:
//  SwiftUI's Text("literal") treats the literal as a LocalizedStringKey and
//  resolves it against the current Locale in the environment. By overriding
//  \.locale at the app root with `resolvedLocale`, choosing French/English in
//  Settings re-renders the whole tree in that language — without changing the
//  device settings.
//

import SwiftUI
import Combine

/// The language the user can pick in Settings.
enum AppLanguage: String, CaseIterable, Identifiable {
    /// Follow the device/system language (default).
    case system
    case english
    case french

    var id: String { rawValue }

    /// Label shown in the picker, in that language's own words.
    var displayName: String {
        switch self {
        case .system:  return NSLocalizedString("language.system", value: "System", comment: "Follow device language")
        case .english: return "English"
        case .french:  return "Français"
        }
    }

    /// The locale to force, or nil to follow the system.
    var locale: Locale? {
        switch self {
        case .system:  return nil
        case .english: return Locale(identifier: "en")
        case .french:  return Locale(identifier: "fr")
        }
    }

    /// The BCP-47 language code used when instructing the LLM which language to
    /// answer in. Resolves `.system` against the current device language,
    /// clamped to the two languages we actually support.
    var llmLanguageCode: String {
        switch self {
        case .english: return "en"
        case .french:  return "fr"
        case .system:
            let preferred = Locale.preferredLanguages.first ?? "en"
            return preferred.lowercased().hasPrefix("fr") ? "fr" : "en"
        }
    }

    /// Human-readable language name for embedding in LLM prompts.
    var llmLanguageName: String {
        llmLanguageCode == "fr" ? "French" : "English"
    }
}

@MainActor
final class LanguageManager: ObservableObject {
    /// The UserDefaults key backing @AppStorage("appLanguage"). Exposed so
    /// non-View code (e.g. the coaching layer) can read the current choice
    /// without a view hierarchy. `nonisolated` so services/agents running off
    /// the main actor can read it.
    nonisolated static let storageKey = "appLanguage"

    @AppStorage(storageKey) private var storedLanguage: String = AppLanguage.system.rawValue

    @Published var current: AppLanguage = .system

    init() {
        current = AppLanguage(rawValue: storedLanguage) ?? .system
        // Re-apply the saved choice to the OS localization preference at launch
        // so bundle lookups match the in-app selection from the first screen.
        applyAppleLanguages(for: current)
    }

    /// The user's selected language, resolved from UserDefaults. Safe to call
    /// from ANY context (services, view models, background tasks) that can't
    /// inject the manager — it only reads UserDefaults, so it's `nonisolated`.
    /// Falls back to `.system` when unset.
    nonisolated static var currentLanguage: AppLanguage {
        let raw = UserDefaults.standard.string(forKey: storageKey) ?? AppLanguage.system.rawValue
        return AppLanguage(rawValue: raw) ?? .system
    }

    /// Persist and apply a new language choice. The environment locale override
    /// reads `resolvedLocale`, so publishing `current` re-renders the UI.
    ///
    /// We also update the standard `AppleLanguages` preference so that the
    /// bundle-based lookups (`String(localized:)`, `NSLocalizedString`, and the
    /// `appLocalized` helper) resolve against the chosen language too — not just
    /// SwiftUI `Text`. This makes coach/service strings follow the in-app switch
    /// as well. Newly created strings pick this up immediately; anything already
    /// on screen refreshes as views re-render.
    func select(_ language: AppLanguage) {
        current = language
        storedLanguage = language.rawValue
        applyAppleLanguages(for: language)
        // Reset the cached per-language bundle so appLocalized() re-resolves.
        AppLocalization.invalidateCache()
        objectWillChange.send()
    }

    /// Points the OS localization machinery at the chosen language (or removes
    /// the override to follow the device when `.system`).
    private func applyAppleLanguages(for language: AppLanguage) {
        let defaults = UserDefaults.standard
        if let code = language.lprojCode {
            defaults.set([code], forKey: "AppleLanguages")
        } else {
            defaults.removeObject(forKey: "AppleLanguages")
        }
    }

    /// Locale to apply to the environment, or the device locale when following
    /// the system.
    var resolvedLocale: Locale {
        current.locale ?? Locale.autoupdatingCurrent
    }

    /// Language descriptor to hand to the coaching/LLM layer.
    var llmLanguageName: String { current.llmLanguageName }
    var llmLanguageCode: String { current.llmLanguageCode }
}

// MARK: - In-app localization for plain (non-Text) strings

extension AppLanguage {
    /// The `.lproj` code for this language, or nil to follow the system.
    var lprojCode: String? {
        switch self {
        case .system:  return nil
        case .english: return "en"
        case .french:  return "fr"
        }
    }
}

/// Resolves a localized string against the language the user picked IN-APP.
///
/// Why this exists: SwiftUI's `Text("literal")` follows the `\.locale`
/// environment override we set at the app root, so static UI localizes
/// correctly. But `String(localized:)` does NOT — it resolves against the
/// app's process language (the OS-level setting), so any string BUILT in a
/// service or view model (coach greeting, suggested prompts, rule-based
/// advice…) stays in the process language and ignores the in-app switch.
///
/// This helper loads the specific `.lproj` bundle for the chosen language and
/// looks the key up there, so those strings follow the in-app selection too.
enum AppLocalization {
    /// Cache of per-language bundles so we don't hit the filesystem each call.
    nonisolated(unsafe) private static var bundleCache: [String: Bundle] = [:]
    private static let cacheLock = NSLock()

    /// Clears the cached bundles so the next lookup re-resolves for a newly
    /// selected language.
    nonisolated static func invalidateCache() {
        cacheLock.lock()
        defer { cacheLock.unlock() }
        bundleCache.removeAll()
    }

    /// The bundle for the user's currently selected in-app language. Falls back
    /// to `.main` when following the system or if the `.lproj` can't be found.
    nonisolated static func currentBundle() -> Bundle {
        guard let code = LanguageManager.currentLanguage.lprojCode else {
            return .main
        }
        cacheLock.lock()
        defer { cacheLock.unlock() }
        if let cached = bundleCache[code] { return cached }
        guard let path = Bundle.main.path(forResource: code, ofType: "lproj"),
              let bundle = Bundle(path: path) else {
            return .main
        }
        bundleCache[code] = bundle
        return bundle
    }
}

/// Localizes `key` against the in-app selected language, with interpolated
/// arguments. Use this instead of `String(localized:)` for strings produced
/// OUTSIDE SwiftUI `Text` (services, view models) that must follow the in-app
/// language switch.
nonisolated func appLocalized(_ key: String, _ args: CVarArg...) -> String {
    let bundle = AppLocalization.currentBundle()
    let format = bundle.localizedString(forKey: key, value: key, table: nil)
    return args.isEmpty ? format : String(format: format, arguments: args)
}
