//
//  RootView.swift
//  nextmove
//
//  Racine de l'app : affiche l'écran de connexion tant que l'utilisateur n'est
//  pas authentifié, puis bascule sur ContentView une fois connecté.
//  Le basculement est piloté par NextMoveAPI.isLoggedIn (publié), donc il est
//  automatique dès qu'une connexion/inscription/déconnexion a lieu.
//

import SwiftUI

struct RootView: View {
    @EnvironmentObject private var api: NextMoveAPI

    var body: some View {
        Group {
            if api.isLoggedIn {
                ContentView()
            } else {
                LoginView()
            }
        }
        .animation(.default, value: api.isLoggedIn)
        .task {
            // Si un token est déjà stocké, on le valide au démarrage.
            // S'il a expiré, fetchMe() déconnecte proprement -> écran de login.
            if api.isLoggedIn {
                try? await api.fetchMe()
            }
        }
    }
}

#Preview {
    RootView().environmentObject(NextMoveAPI())
}
