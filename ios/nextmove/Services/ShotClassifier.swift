//
//  ShotClassifier.swift
//  nextmove
//
//  Tier-2b interface for SHOT-TYPE classification (serve / volley / dink /
//  overhead / groundstroke). This is the biggest honest gap between NextMove
//  and products like PB Vision, and this file is written to make the gap — and
//  the path to closing it — explicit.
//
//  WHY A SEPARATE, EXPLICIT INTERFACE?
//  --------------------------------------------------------------------------
//  Bounding-box detection alone CANNOT reliably tell shot types apart: a serve,
//  a volley and a groundstroke can all look like "player + ball" boxes. Telling
//  them apart needs the player's BODY POSE (arm above head → serve/overhead;
//  contact low and soft near the net → dink; etc.). We do not ship a pose model
//  yet, so we must not pretend to measure shot types.
//
//  This file therefore provides:
//    1. `ShotClassifier` — the protocol the rest of the app can depend on.
//    2. `ShotType` with an `.unknown` case and a `confidence`, so callers always
//       know when a label is a guess.
//    3. `HeuristicShotClassifier` — a transparent, trajectory-only fallback that
//       makes a COARSE guess (overhead vs net vs groundstroke) from ball height
//       and speed, and honestly returns `.unknown` with low confidence when it
//       can't tell. No fabricated per-shot ratings.
//    4. `PoseShotClassifier` — a documented placeholder showing exactly where a
//       Core ML pose model (e.g. an Apple Vision body-pose request or a bundled
//       pose .mlmodel) would plug in. It is intentionally not implemented and
//       says so, rather than returning fake data.
//

import Foundation
import CoreGraphics

// MARK: - Shot type

/// A classified shot with an explicit confidence and an `.unknown` escape
/// hatch. Callers should treat anything below ~0.5 confidence as "not sure".
enum ShotType: String, Codable {
    case serve
    case `return`
    case volley
    case dink
    case overhead      // smash / bandeja family
    case groundstroke
    case unknown

    var displayName: String {
        switch self {
        case .serve: return "Serve"
        case .return: return "Return"
        case .volley: return "Volley"
        case .dink: return "Dink"
        case .overhead: return "Overhead"
        case .groundstroke: return "Groundstroke"
        case .unknown: return "Unknown"
        }
    }
}

/// Result of classifying a single shot.
struct ShotClassification: Codable, Identifiable {
    let id: UUID
    let type: ShotType
    let confidence: Float   // 0–1; honesty signal, not marketing
    let timestamp: TimeInterval

    init(id: UUID = UUID(), type: ShotType, confidence: Float, timestamp: TimeInterval) {
        self.id = id
        self.type = type
        self.confidence = confidence
        self.timestamp = timestamp
    }
}

/// One shot's observable context, assembled by the caller from existing
/// detections/tracks. Kept deliberately small so both the heuristic and a
/// future pose model can consume it.
struct ShotContext {
    /// Ball centre trajectory (normalised, top-left origin) over the shot.
    let ballTrajectory: [CGPoint]
    /// The striking player's box at contact, if known (normalised).
    let playerBox: CGRect?
    /// Index of this shot within its rally (0 = first = serve candidate).
    let indexInRally: Int
    /// Shot time (seconds) for reporting.
    let timestamp: TimeInterval
}

// MARK: - Protocol

/// Classifies shots from context. Implementations range from a transparent
/// trajectory heuristic (today) to a pose-model-backed classifier (next).
protocol ShotClassifier {
    func classify(_ context: ShotContext) -> ShotClassification
}

// MARK: - Heuristic (ships today, honest about its limits)

/// Trajectory-only classifier. Makes a COARSE, explainable guess and returns
/// `.unknown` when the signal is ambiguous. It intentionally does NOT attempt
/// fine labels (serve vs return vs drive) that need pose; it separates the few
/// cases ball motion can actually support.
struct HeuristicShotClassifier: ShotClassifier {

    func classify(_ context: ShotContext) -> ShotClassification {
        let traj = context.ballTrajectory
        guard traj.count >= 2 else {
            return ShotClassification(type: .unknown, confidence: 0.2, timestamp: context.timestamp)
        }

        // y grows downward: small y = high in frame (up near the top), large y =
        // low (near the ground / near camera).
        let minY = traj.map { $0.y }.min() ?? 0.5
        let avgY = traj.map { $0.y }.reduce(0, +) / CGFloat(traj.count)

        // Rough speed proxy: total path length over the number of steps.
        var pathLen: CGFloat = 0
        for i in 1..<traj.count {
            pathLen += hypot(traj[i].x - traj[i-1].x, traj[i].y - traj[i-1].y)
        }
        let speed = pathLen / CGFloat(traj.count - 1)

        // 1) First shot of a rally that starts high → serve candidate. Still a
        //    guess (pose would confirm the overhead motion), so moderate conf.
        if context.indexInRally == 0 && minY < 0.35 {
            return ShotClassification(type: .serve, confidence: 0.55, timestamp: context.timestamp)
        }

        // 2) Ball peaks very high in frame with a fast descent → overhead/smash.
        if minY < 0.25 && speed > 0.06 {
            return ShotClassification(type: .overhead, confidence: 0.5, timestamp: context.timestamp)
        }

        // 3) Slow, low, near-net exchange → dink.
        if speed < 0.03 && avgY > 0.55 {
            return ShotClassification(type: .dink, confidence: 0.5, timestamp: context.timestamp)
        }

        // 4) Otherwise we genuinely cannot tell a volley from a groundstroke
        //    without pose. Be honest.
        return ShotClassification(type: .unknown, confidence: 0.3, timestamp: context.timestamp)
    }
}

// MARK: - Pose-backed (the real upgrade — intentionally not implemented)

/// Placeholder for the pose-model-backed classifier. This is where tier-2b is
/// genuinely closed. The integration shape is documented so the work is scoped,
/// but it deliberately returns `.unknown` instead of inventing results.
///
/// Integration plan (next increment):
///   1. Run a body-pose request on the striking player's crop at contact —
///      either Apple's Vision `VNDetectHumanBodyPoseRequest`, or a bundled
///      pose `.mlmodel` (e.g. a lightweight MoveNet/HRNet export) for more
///      control and cross-sport consistency.
///   2. From the joints (wrist/elbow/shoulder relative to head/hip), derive the
///      contact height and swing plane:
///        • wrist above head at contact → serve / overhead
///        • contact in front, waist height, net-side → volley
///        • contact low and soft near the net → dink
///        • contact beside the body from the back court → groundstroke
///   3. Combine pose evidence with the trajectory heuristic (sensor fusion):
///      pose decides the type, trajectory confirms direction/speed, and the
///      reported `confidence` reflects their agreement.
///
/// Until that model is wired in, this type is a visible TODO, not a silent one.
struct PoseShotClassifier: ShotClassifier {

    /// Fallback used until a pose model is integrated.
    private let fallback: ShotClassifier

    /// `isPoseModelAvailable` stays false until a pose model is bundled and
    /// loaded. When false, we defer to the heuristic rather than fabricate.
    let isPoseModelAvailable: Bool

    init(fallback: ShotClassifier = HeuristicShotClassifier(), isPoseModelAvailable: Bool = false) {
        self.fallback = fallback
        self.isPoseModelAvailable = isPoseModelAvailable
    }

    func classify(_ context: ShotContext) -> ShotClassification {
        guard isPoseModelAvailable else {
            // No pose model yet → delegate to the honest heuristic. We do NOT
            // claim pose-level accuracy we don't have.
            return fallback.classify(context)
        }
        // TODO(tier-2b): run pose request on context.playerBox crop, derive the
        // shot type from joint geometry, fuse with the trajectory heuristic.
        // Intentionally unreachable today (isPoseModelAvailable == false).
        return fallback.classify(context)
    }
}
