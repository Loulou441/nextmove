//
//  LoginView.swift
//  nextmove
//
//  Écran de connexion iOS — connexion RÉELLE via NextMoveAPI contre le backend
//  partagé. Présenté par RootView tant que l'utilisateur n'est pas connecté.
//

import SwiftUI

struct LoginView: View {
    @EnvironmentObject private var api: NextMoveAPI

    // Persisté ici pour que ContentView/SportManager ouvre directement sur le
    // sport choisi à l'inscription, sans re-demander via la modale.
    @AppStorage("selectedSport") private var storedSport: String = ""

    @State private var email = ""
    @State private var password = ""
    @State private var isRegistering = false
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var selectedSport: SportType = .pickleball

    var body: some View {
        VStack(spacing: 24) {
            Spacer()

            VStack(spacing: 16) {
                // Logo de marque (marque + mot-symbole) sur sa carte verte.
                // Le visuel est autoporté : il reste lisible en clair et en
                // sombre, donc pas de fond supplémentaire ici.
                Image("LogoMark")
                    .resizable()
                    .scaledToFit()
                    .frame(maxWidth: 260)
                    .clipShape(RoundedRectangle(cornerRadius: 20))
                    .accessibilityLabel("NextMove")

                Text(isRegistering ? "Créer un compte" : "Connexion")
                    .font(.headline)
                    .foregroundStyle(.secondary)
            }

            VStack(spacing: 14) {
                TextField("Email", text: $email)
                    .textContentType(.emailAddress)
                    .keyboardType(.emailAddress)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .textFieldStyle(.roundedBorder)

                SecureField("Mot de passe", text: $password)
                    .textContentType(isRegistering ? .newPassword : .password)
                    .textFieldStyle(.roundedBorder)

                // À l'inscription, l'utilisateur choisit le sport qu'il veut
                // analyser. Ce choix est envoyé comme preferred_sport et
                // pré-sélectionne le sport à l'ouverture de l'app.
                if isRegistering {
                    sportPicker
                        .transition(.opacity.combined(with: .move(edge: .top)))
                }

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
                    .background(canSubmit ? Color.green : Color.gray)
                    .foregroundStyle(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                }
                .disabled(!canSubmit || isLoading)

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

    /// Sélecteur de sport présenté à l'inscription. Une rangée de pastilles
    /// tappables ; la sélection est mise en évidence par la couleur du sport.
    private var sportPicker: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Quel sport veux-tu analyser ?")
                .font(.subheadline)
                .foregroundStyle(.secondary)

            HStack(spacing: 10) {
                ForEach(SportType.allCases) { sport in
                    sportChip(sport)
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func sportChip(_ sport: SportType) -> some View {
        let isSelected = selectedSport == sport
        return Button {
            withAnimation(.easeInOut(duration: 0.15)) { selectedSport = sport }
        } label: {
            VStack(spacing: 6) {
                Group {
                    if let assetName = sport.assetIconName {
                        Image(assetName).resizable().scaledToFit()
                    } else {
                        Text(sport.icon).font(.system(size: 30))
                    }
                }
                .frame(height: 36)

                Text(sport.displayName)
                    .font(.caption2)
                    .fontWeight(isSelected ? .semibold : .regular)
                    .foregroundStyle(isSelected ? .primary : .secondary)
                    .lineLimit(1)
                    .minimumScaleFactor(0.7)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 10)
            .background(sport.color.opacity(isSelected ? 0.18 : 0.06))
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(isSelected ? sport.color : .clear, lineWidth: 2)
            )
        }
        .buttonStyle(.plain)
        .accessibilityLabel(sport.displayName)
        .accessibilityAddTraits(isSelected ? [.isSelected] : [])
    }

    private var canSubmit: Bool {
        !email.isEmpty && password.count >= 6
    }

    private func submit() {
        errorMessage = nil
        isLoading = true
        Task {
            defer { isLoading = false }
            do {
                if isRegistering {
                    _ = try await api.register(
                        email: email,
                        password: password,
                        preferredSport: selectedSport.rawValue
                    )
                    // Ouvre directement l'app sur le sport choisi (évite la
                    // modale de sélection au premier lancement).
                    storedSport = selectedSport.rawValue
                } else {
                    _ = try await api.login(email: email, password: password)
                }
                // À la connexion réussie, RootView bascule automatiquement sur
                // ContentView grâce à api.isLoggedIn.
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }
}

#Preview {
    LoginView().environmentObject(NextMoveAPI())
}
