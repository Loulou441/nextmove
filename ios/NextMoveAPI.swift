//
//  NextMoveAPI.swift
//  nextmove
//
//  Client réseau pour l'API partagée (FastAPI). La connexion iOS est RÉELLE :
//  elle appelle /auth/login sur le même backend que l'app web, récupère un
//  token JWT, le conserve, et l'envoie en Bearer sur les requêtes protégées.
//
//  Intégration : déplacer ce fichier dans `nextmove/Services/` du projet Xcode
//  (branche feature/ios-app) et l'ajouter à la cible de l'app.
//

import Foundation

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

/// Client de l'API NextMove. Instancier une fois (ex. en @StateObject) et
/// partager dans l'app. Le token est persisté pour garder l'utilisateur connecté.
@MainActor
final class NextMoveAPI: ObservableObject {

    /// URL de base de l'API. En simulateur : http://localhost:8000
    /// Sur un iPhone physique, remplacer par l'IP de la machine (ex. http://192.168.1.20:8000).
    private let baseURL: URL

    /// Token de session courant (nil = déconnecté). Persisté dans UserDefaults
    /// pour rester connecté entre deux lancements — cohérent avec le stockage
    /// actuel de l'app (RecordingViewModel utilise déjà UserDefaults).
    @Published private(set) var token: String?
    @Published private(set) var currentUser: APIUser?

    private let tokenKey = "nextmove_auth_token"

    init(baseURL: URL = URL(string: "http://localhost:8000")!) {
        self.baseURL = baseURL
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
    @discardableResult
    func fetchMe() async throws -> APIUser {
        let user: APIUser = try await get("/auth/me")
        currentUser = user
        return user
    }

    // MARK: Données

    /// Liste les matchs de l'utilisateur connecté (les mêmes que sur le web).
    func fetchMatches() async throws -> [APIMatch] {
        try await get("/matches")
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
