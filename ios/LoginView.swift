//
//  LoginView.swift
//  nextmove
//
//  Écran de connexion iOS — connexion RÉELLE via NextMoveAPI contre le backend
//  partagé. À intégrer dans `nextmove/Views/` (branche feature/ios-app) et à
//  présenter au lancement tant que `api.isLoggedIn == false`.
//

import SwiftUI

struct LoginView: View {
    @EnvironmentObject private var api: NextMoveAPI

    @State private var email = ""
    @State private var password = ""
    @State private var isRegistering = false
    @State private var isLoading = false
    @State private var errorMessage: String?

    var body: some View {
        VStack(spacing: 24) {
            Spacer()

            VStack(spacing: 8) {
                Text("NextMove")
                    .font(.largeTitle.bold())
                Text(isRegistering ? "Créer un compte" : "Connexion")
                    .font(.headline)
                    .foregroundStyle(.secondary)
            }

            VStack(spacing: 14) {
                TextField("Email", text: $email)
                    .textContentType(.emailAddress)
                    .keyboardType(.emailAddress)
                    .autocapitalization(.none)
                    .textFieldStyle(.roundedBorder)

                SecureField("Mot de passe", text: $password)
                    .textContentType(isRegistering ? .newPassword : .password)
                    .textFieldStyle(.roundedBorder)

                if let errorMessage {
                    Text(errorMessage)
                        .font(.footnote)
                        .foregroundStyle(.red)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }

                Button(action: submit) {
                    HStack {
                        if isLoading { ProgressView().tint(.white) }
                        Text(isRegistering ? "S'inscrire" : "Se connecter")
                            .bold()
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.accentColor)
                    .foregroundStyle(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                }
                .disabled(isLoading || email.isEmpty || password.isEmpty)

                Button(isRegistering ? "J'ai déjà un compte" : "Créer un compte") {
                    withAnimation { isRegistering.toggle(); errorMessage = nil }
                }
                .font(.footnote)
            }
            .padding(.horizontal, 32)

            Spacer()
        }
        .padding()
    }

    private func submit() {
        errorMessage = nil
        isLoading = true
        Task {
            defer { isLoading = false }
            do {
                if isRegistering {
                    _ = try await api.register(email: email, password: password)
                } else {
                    _ = try await api.login(email: email, password: password)
                }
                // À la connexion réussie, l'app bascule automatiquement sur son
                // contenu principal (piloté par api.isLoggedIn dans la vue racine).
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }
}
