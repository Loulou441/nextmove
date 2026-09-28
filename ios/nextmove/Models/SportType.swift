//
//  SportType.swift
//  nextmove
//
//  Created by Asmae  on 09/03/2026.
//

import SwiftUI

enum SportType: String, Codable, CaseIterable, Identifiable {
    case pickleball
    case padel
    case tennis
    case badminton

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .pickleball:
            return "Pickleball"
        case .padel:
            return "Padel"
        case .tennis:
            return "Tennis"
        case .badminton:
            return "Badminton"
        }
    }

    /// Emoji fallback icon. Used for sports without a bundled image asset
    /// (badminton), and as a safety net if an asset fails to load.
    var icon: String {
        switch self {
        case .pickleball:
            return "🏓"
        case .padel:
            return "🎾"
        case .tennis:
            return "🎾"
        case .badminton:
            return "🏸"
        }
    }

    /// Name of the brand image asset in Assets.xcassets, when one exists.
    /// Badminton has no dedicated artwork, so it falls back to the emoji.
    var assetIconName: String? {
        switch self {
        case .pickleball:
            return "SportPickleball"
        case .padel:
            return "SportPadel"
        case .tennis:
            return "SportTennis"
        case .badminton:
            return nil
        }
    }

    var description: String {
        switch self {
        case .pickleball:
            return String(localized: "Fast-paced paddle sport")
        case .padel:
            return String(localized: "Enclosed-court racket sport")
        case .tennis:
            return String(localized: "Classic racket sport")
        case .badminton:
            return String(localized: "Fast net-divided racket sport")
        }
    }

    var color: Color {
        switch self {
        case .pickleball:
            return .green
        case .padel:
            return .blue
        case .tennis:
            return .yellow
        case .badminton:
            return .red
        }
    }

    /// Whether this sport is a racket/paddle sport (shares coaching vocabulary).
    /// The app is focused exclusively on racket sports, so this is always true;
    /// kept for call sites that branch on racket-sport behaviour.
    var isRacketSport: Bool {
        true
    }
}
