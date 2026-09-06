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

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(api)
        }
    }
}
