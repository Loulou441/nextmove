//
//  PlayerStats.swift
//  nextmove
//
//  Computes performance stats scoped to ONE selected player (the figure the
//  user tapped), from that player's own detections. This is what powers the
//  PB-Vision-style per-player view (`/player/N`): the same clip, but every
//  number is about the chosen person rather than the court as a whole.
//
//  HONEST SCOPE:
//  Coverage, zone distribution and activity are measured DIRECTLY from the
//  selected player's bounding-box positions over time — these are real,
//  per-player measurements. Shot-type breakdowns (serve/volley/dink) are NOT
//  computed here because bounding boxes alone can't tell shot types apart;
//  that needs pose estimation (see ShotClassifier.swift). We expose only what
//  we can honestly measure per player.
//

import Foundation
import CoreGraphics

/// A compact, per-player performance summary derived from one player's own
/// detections. All values are measured, not synthesised.
struct PlayerStats: Codable {
    /// How much of the court the player used, as a % of frame area (convex
    /// hull of their positions). Higher = more mobile / wider coverage.
    let coveragePercent: Double

    /// Time share spent in each court zone (3×3 grid), summing to 1.0.
    let zoneDistribution: [String: Double]

    /// Left/right balance in [-1, 1]: negative favours left, positive right.
    let leftRightBalance: Double

    /// Average front/back position (0 = baseline, 1 = net side) — tells whether
    /// the player tends to hold the net or hang at the back.
    let averageDepth: Double

    /// Number of detections attributed to this player (activity / sample size).
    let detectionCount: Int

    /// Mean detection confidence for this player (0–1) — a data-quality signal.
    let averageConfidence: Double
}

/// Derives a per-player VIEW of a match-level `GameAnalysis`.
///
/// HONEST SCOPE — which numbers are truly per-player and which are not:
///  • Court coverage and the **Movement** skill are measured from the selected
///    player's own positions → genuinely per-player.
///  • The **overall rating** is recomputed by substituting that player's
///    movement/coverage into the blend, so it shifts per player.
///  • Ball-based figures (rallies, winners, serve/return/third/dink/volley
///    skills) come from the ball trajectory, which belongs to the MATCH, not one
///    person — we cannot split them per player without pose. They are kept as-is
///    and should be presented as match context, not personal shot grades.
enum PlayerAnalysisAdapter {

    /// Returns a copy of `base` with the per-player-derivable fields adjusted to
    /// the given player. Fields we can't honestly attribute per player are left
    /// unchanged.
    static func analysis(for candidate: PlayerCandidate, base: GameAnalysis) -> GameAnalysis {
        let stats = PlayerStatsCalculator.stats(for: candidate)
        var out = base

        // Movement skill (0–5) from this player's own court coverage. Coverage is
        // a % of frame; ~25% hull area is already strong lateral+depth movement.
        let movement = min(5.0, (stats.coveragePercent / 25.0) * 5.0)

        var skills = base.skillRatings
        skills.movement = movement
        out.skillRatings = skills

        // Court coverage stat → this player's measured coverage.
        var statistics = base.statistics
        statistics.courtCoveragePercent = stats.coveragePercent
        out.statistics = statistics

        // Overall rating: re-blend so changing player visibly changes the score.
        // Keep the match-derived ball skills, but swap in this player's movement.
        // Average only the skills that carry a real signal (as the pipeline does).
        let allSkills = [skills.serve, skills.return, skills.thirdShot,
                         skills.dinking, skills.volleys, skills.movement]
        let measured = allSkills.filter { $0 > 0 }
        if !measured.isEmpty {
            out.overallRating = (measured.reduce(0, +) / Double(measured.count))
        }

        return out
    }
}

/// Computes `PlayerStats` for a single `PlayerCandidate`.
///
/// Mirrors the measurement conventions used elsewhere in the app
/// (`FeatureExtractor.computeCourtCoverage`): y grows downward, the 3×3 grid
/// uses the same thresholds, and coverage is a convex-hull area so it is
/// directly comparable to the match-level number.
enum PlayerStatsCalculator {

    /// Builds per-player stats from the candidate's own tracked positions.
    static func stats(for candidate: PlayerCandidate) -> PlayerStats {
        let points = candidate.positions
        guard !points.isEmpty else {
            return PlayerStats(
                coveragePercent: 0, zoneDistribution: [:], leftRightBalance: 0,
                averageDepth: 0, detectionCount: 0, averageConfidence: 0
            )
        }

        // --- Coverage: convex-hull area as % of the frame -------------------
        let coverage = convexHullAreaPercent(points)

        // --- Zone distribution (3×3), same thresholds as FeatureExtractor ---
        var zoneCounts: [String: Int] = [:]
        var leftCount = 0
        var rightCount = 0
        var depthSum: Double = 0
        for p in points {
            let xZone = p.x < 0.33 ? "Left" : (p.x < 0.67 ? "Center" : "Right")
            let yZone = p.y < 0.33 ? "back" : (p.y < 0.67 ? "mid" : "front")
            zoneCounts[yZone + xZone, default: 0] += 1
            if p.x < 0.5 { leftCount += 1 } else { rightCount += 1 }
            depthSum += Double(p.y)
        }
        let total = Double(points.count)
        let zoneDistribution = zoneCounts.mapValues { Double($0) / total }
        let sides = leftCount + rightCount
        let balance = sides > 0 ? (Double(rightCount) - Double(leftCount)) / Double(sides) : 0.0

        return PlayerStats(
            coveragePercent: coverage,
            zoneDistribution: zoneDistribution,
            leftRightBalance: balance,
            averageDepth: depthSum / total,
            detectionCount: points.count,
            averageConfidence: Double(candidate.averageConfidence)
        )
    }

    // MARK: - Convex hull area (Andrew's monotone chain)

    /// Area of the convex hull of normalised points, expressed as a percentage
    /// of the full frame (0–100). Fewer than 3 points → 0.
    private static func convexHullAreaPercent(_ pts: [CGPoint]) -> Double {
        guard pts.count >= 3 else { return 0 }

        let sorted = pts.sorted { $0.x != $1.x ? $0.x < $1.x : $0.y < $1.y }

        func cross(_ o: CGPoint, _ a: CGPoint, _ b: CGPoint) -> CGFloat {
            (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)
        }

        var lower: [CGPoint] = []
        for p in sorted {
            while lower.count >= 2 && cross(lower[lower.count - 2], lower[lower.count - 1], p) <= 0 {
                lower.removeLast()
            }
            lower.append(p)
        }
        var upper: [CGPoint] = []
        for p in sorted.reversed() {
            while upper.count >= 2 && cross(upper[upper.count - 2], upper[upper.count - 1], p) <= 0 {
                upper.removeLast()
            }
            upper.append(p)
        }
        // Concatenate, dropping the duplicated endpoints.
        let hull = lower.dropLast() + upper.dropLast()
        let h = Array(hull)
        guard h.count >= 3 else { return 0 }

        // Shoelace area (normalised 0–1 coords) → % of frame.
        var area: CGFloat = 0
        for i in 0..<h.count {
            let j = (i + 1) % h.count
            area += h[i].x * h[j].y - h[j].x * h[i].y
        }
        area = abs(area) / 2.0
        return min(100.0, Double(area) * 100.0)
    }
}
