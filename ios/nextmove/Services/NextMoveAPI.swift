//
//  NextMoveAPI.swift
//  nextmove
//
//  Client réseau pour l'API partagée (FastAPI). La connexion iOS est RÉELLE :
//  elle appelle /auth/login sur le même backend que l'app web, récupère un
//  token JWT, le conserve, et l'envoie en Bearer sur les requêtes protégées.
//

import Foundation
import Combine

// MARK: - Modèles renvoyés par l'API

struct APIUser: Codable, Identifiable {
    let id: String
    let email: String
    let preferredSport: String
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case id, email
        case preferredSport = "preferred_sport"
        case createdAt = "created_at"
    }
}

struct AuthResponse: Codable {
    let accessToken: String
    let tokenType: String
    let user: APIUser

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case tokenType = "token_type"
        case user
    }
}

struct APIMatch: Codable, Identifiable {
    let id: String
    let title: String
    let sport: String
    let status: String
    let rating: Double?
    let rallies: Int?
    let winners: Int?
    let errors: Int?
    let coverage: Int?
}

// MARK: - Coach IA (agents RAG partagés avec le web)

/// Une séquence de jeu envoyée au coach RAG du backend.
struct CoachSequenceInput: Codable {
    var timestamp: String
    var evenement_cle: String
    var contexte_tactique: String
    // Métriques libres (clé -> valeur texte). Simple et suffisant pour le RAG.
    var metriques_video: [String: String]
}

struct CoachRecommendationsRequest: Codable {
    let sport: String
    let sequences: [CoachSequenceInput]
    let joueur: [String: String]
}

struct CoachRecommendationContent: Codable {
    let constat: String
    let analyse: String
    let action_corrective: String
    let pro_tip: String?
    let exercice_source_id: String?
}

struct CoachRecommendation: Codable, Identifiable {
    var id: String { timestamp + titre }
    let timestamp: String
    let titre: String
    let contenu: CoachRecommendationContent
}

struct CoachRecommendationsResponse: Codable {
    let sport: String
    let recommandations_coach: [CoachRecommendation]
}

enum APIError: LocalizedError {
    case invalidResponse
    case unauthorized
    case server(String)

    var errorDescription: String? {
        switch self {
        case .invalidResponse: return "Réponse invalide du serveur."
        case .unauthorized: return "Email ou mot de passe incorrect."
        case .server(let msg): return msg
        }
    }
}

// MARK: - Client

/// Client de l'API NextMove, injecté comme EnvironmentObject depuis l'app.
/// Le token est persisté pour garder l'utilisateur connecté entre deux lancements.
@MainActor
final class NextMoveAPI: ObservableObject {

    /// URL de base de l'API.
    /// - Simulateur : http://localhost:8000
    /// - iPhone physique : http://<IP-de-votre-Mac>:8000 (même réseau Wi-Fi).
    private let baseURL: URL

    @Published private(set) var token: String?
    @Published private(set) var currentUser: APIUser?

    private let tokenKey = "nextmove_auth_token"

    /// Résout l'URL de base dans cet ordre de priorité :
    ///   1. Argument explicite (tests unitaires, previews).
    ///   2. Variable d'environnement NEXTMOVE_API_URL (schéma Xcode / CI).
    ///   3. Clé Info.plist NEXTMOVE_API_URL (réglage par target sans recompiler).
    ///   4. Simulateur  → http://localhost:8000
    ///   5. Appareil physique → http://192.168.1.175:8000 (IP LAN par défaut).
    ///
    /// Pour changer d'IP sans recompiler : ajouter la clé NEXTMOVE_API_URL
    /// dans Info.plist (ou dans le schéma Xcode > Run > Arguments > Environment).
    private static var resolvedBaseURL: URL {
        // 1. Variable d'environnement (schéma Xcode ou CI)
        if let raw = ProcessInfo.processInfo.environment["NEXTMOVE_API_URL"],
           let url = URL(string: raw.trimmingCharacters(in: .whitespacesAndNewlines)),
           url.scheme != nil {
            return url
        }
        // 2. Info.plist
        if let raw = Bundle.main.object(forInfoDictionaryKey: "NEXTMOVE_API_URL") as? String,
           !raw.isEmpty,
           let url = URL(string: raw.trimmingCharacters(in: .whitespacesAndNewlines)),
           url.scheme != nil {
            return url
        }
        // 3. Défauts selon la cible de compilation
        #if targetEnvironment(simulator)
        return URL(string: "http://localhost:8000")!
        #else
        // Appareil physique : localhost pointerait vers l'iPhone.
        // Changer cette valeur dans Info.plist > NEXTMOVE_API_URL pour éviter
        // de recompiler à chaque changement d'IP sur le réseau.
        return URL(string: "http://192.168.1.175:8000")!
        #endif
    }

    init(baseURL: URL? = nil) {
        self.baseURL = baseURL ?? Self.resolvedBaseURL
        self.token = UserDefaults.standard.string(forKey: tokenKey)
    }

    var isLoggedIn: Bool { token != nil }

    // MARK: Authentification

    /// Inscription. Renvoie l'utilisateur et connecte la session.
    func register(email: String, password: String, preferredSport: String = "pickleball") async throws -> APIUser {
        let body = ["email": email, "password": password, "preferred_sport": preferredSport]
        let auth: AuthResponse = try await post("/auth/register", body: body)
        applySession(auth)
        return auth.user
    }

    /// Connexion réelle contre /auth/login (même backend que le web).
    func login(email: String, password: String) async throws -> APIUser {
        let body = ["email": email, "password": password]
        let auth: AuthResponse = try await post("/auth/login", body: body)
        applySession(auth)
        return auth.user
    }

    /// Déconnexion locale (efface le token).
    func logout() {
        token = nil
        currentUser = nil
        UserDefaults.standard.removeObject(forKey: tokenKey)
    }

    /// Valide le token courant auprès du serveur et rafraîchit l'utilisateur.
    /// À appeler au démarrage : si le token a expiré, on déconnecte proprement.
    @discardableResult
    func fetchMe() async throws -> APIUser {
        do {
            let user: APIUser = try await get("/auth/me")
            currentUser = user
            return user
        } catch APIError.unauthorized {
            logout()
            throw APIError.unauthorized
        }
    }

    // MARK: Données

    /// Liste les matchs de l'utilisateur connecté (les mêmes que sur le web).
    func fetchMatches() async throws -> [APIMatch] {
        try await get("/matches")
    }

    /// Demande au coach RAG du backend (mêmes agents que le web) des
    /// recommandations structurées pour des séquences de jeu.
    /// Nécessite une session (token) — le coaching est propre à l'utilisateur.
    func fetchCoachRecommendations(
        sport: String,
        sequences: [CoachSequenceInput],
        joueur: [String: String] = [:]
    ) async throws -> CoachRecommendationsResponse {
        let payload = CoachRecommendationsRequest(sport: sport, sequences: sequences, joueur: joueur)
        return try await postEncodable("/coach/recommendations", body: payload)
    }

    // MARK: - Bas niveau

    private func applySession(_ auth: AuthResponse) {
        token = auth.accessToken
        currentUser = auth.user
        UserDefaults.standard.set(auth.accessToken, forKey: tokenKey)
    }

    private func get<T: Decodable>(_ path: String) async throws -> T {
        try await request(path, method: "GET", body: Optional<[String: String]>.none)
    }

    private func post<T: Decodable>(_ path: String, body: [String: String]) async throws -> T {
        try await request(path, method: "POST", body: body)
    }

    /// POST avec un corps Encodable arbitraire (JSON imbriqué). Utilisé par le
    /// coach RAG dont la requête n'est pas un simple dictionnaire [String:String].
    private func postEncodable<Body: Encodable, T: Decodable>(_ path: String, body: Body) async throws -> T {
        var req = URLRequest(url: baseURL.appendingPathComponent(path))
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token {
            req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        req.httpBody = try JSONEncoder().encode(body)
        // Le coach RAG peut être lent au premier appel (chargement du modèle
        // d'embedding côté serveur) — on laisse une marge confortable.
        req.timeoutInterval = 120

        let (data, response) = try await URLSession.shared.data(for: req)
        guard let http = response as? HTTPURLResponse else { throw APIError.invalidResponse }

        switch http.statusCode {
        case 200...299:
            return try JSONDecoder().decode(T.self, from: data)
        case 401, 403:
            throw APIError.unauthorized
        default:
            let detail = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["detail"] as? String
            throw APIError.server(detail ?? "Erreur serveur (\(http.statusCode)).")
        }
    }

    private func request<T: Decodable>(_ path: String, method: String, body: [String: String]?) async throws -> T {
        var req = URLRequest(url: baseURL.appendingPathComponent(path))
        req.httpMethod = method
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token {
            req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        if let body {
            req.httpBody = try JSONSerialization.data(withJSONObject: body)
        }

        let (data, response) = try await URLSession.shared.data(for: req)
        guard let http = response as? HTTPURLResponse else { throw APIError.invalidResponse }

        switch http.statusCode {
        case 200...299:
            return try JSONDecoder().decode(T.self, from: data)
        case 401, 403:
            throw APIError.unauthorized
        default:
            let detail = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["detail"] as? String
            throw APIError.server(detail ?? "Erreur serveur (\(http.statusCode)).")
        }
    }
}
