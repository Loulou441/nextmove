//
//  nextmoveApp.swift
//  nextmove
//
//  Created by Asmae  on 09/03/2026.
//
import SwiftUI

@main
struct nextmoveApp: App {
    // Client de l'API partagée, injecté dans toute l'app.
    @StateObject private var api = NextMoveAPI()
    // Langue de l'app (Système / English / Français), injectée partout.
    @StateObject private var languageManager = LanguageManager()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(api)
                .environmentObject(languageManager)
                // Force la langue choisie dans les réglages sur tout l'arbre de
                // vues. `Text("literal")` se résout contre cette Locale.
                .environment(\.locale, languageManager.resolvedLocale)
        }
    }
}
