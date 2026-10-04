//
//  PlayerIdentification.swift
//  nextmove
//
//  Groups raw player detections into a small set of persistent "player
//  candidates" so the user can tap the figure that is them (PB-Vision-style
//  per-player view), and so metrics can be scoped to that one player.
//
//  HONEST SCOPE (read before defending this):
//  --------------------------------------------------------------------------
//  This is player *identification by selection*, not biometric identity.
//  We cluster player detections by their court position so that the two/four
//  people on court become stable candidates WITHIN a clip, extract a
//  representative crop (thumbnail) for each, and let the user pick themselves.
//  It does NOT do appearance-based re-identification (shirt colour / body
//  embedding), so a player who leaves the frame for a long time and returns on
//  the other side could, in a hard case, merge with another cluster. That
//  robustness step (re-ID) is the documented next increment — see
//  ShotClassifier.swift / the roadmap. We prefer saying this plainly over
//  claiming full multi-player tracking we have not built.
//

import Foundation
import CoreGraphics
import AVFoundation

// MARK: - Player Candidate

/// A persistent on-court player the user can select. Built from the raw
/// player `Detection`s of one analysis, grouped by court position.
struct PlayerCandidate: Identifiable, Codable {
    let id: UUID

    /// 1-based label shown in the UI ("Player 1", "Player 2", ...). Ordered so
    /// that index 1 is the near-side player (closest to the camera = most
    /// likely the user), matching the PB Vision `/player/1` convention.
    let index: Int

    /// This candidate's box-centre positions over time (normalised 0–1,
    /// top-left origin), one per detection, in time order. This is all the
    /// downstream stats (coverage/zones/depth) need — we keep positions rather
    /// than the full `Detection` objects so a candidate stays lightweight and
    /// cheap to persist on `GameRecording`.
    let positions: [CGPoint]

    /// Average normalised court position (0–1). `y` grows downward, so a higher
    /// `y` means closer to the camera (near side).
    let averagePosition: CGPoint

    /// Frame number of the single best detection to crop a thumbnail from
    /// (largest, most confident box — the clearest view of this player).
    let thumbnailFrameNumber: Int

    /// Presentation time of that best detection, used to seek the video when
    /// generating the thumbnail crop (avoids a frame→time conversion).
    let thumbnailTime: CMTime

    /// Bounding box (normalised 0–1) to crop for the thumbnail, taken from the
    /// same best detection as `thumbnailFrameNumber`.
    let thumbnailBoundingBox: CGRect

    /// Mean detection confidence for this candidate (0–1).
    let averageConfidence: Float

    /// True for the candidate the system defaults to (near-side player).
    let isLikelyUser: Bool

    /// Court position label built from side (near/far) and lane (left/right),
    /// e.g. "Near Left". For doubles this makes the four players distinguishable
    /// at a glance; the UI shows it under the thumbnail.
    let courtLabel: String

    init(
        id: UUID = UUID(),
        index: Int,
        positions: [CGPoint],
        averagePosition: CGPoint,
        thumbnailFrameNumber: Int,
        thumbnailTime: CMTime,
        thumbnailBoundingBox: CGRect,
        averageConfidence: Float,
        isLikelyUser: Bool,
        courtLabel: String = ""
    ) {
        self.id = id
        self.index = index
        self.positions = positions
        self.averagePosition = averagePosition
        self.thumbnailFrameNumber = thumbnailFrameNumber
        self.thumbnailTime = thumbnailTime
        self.thumbnailBoundingBox = thumbnailBoundingBox
        self.averageConfidence = averageConfidence
        self.isLikelyUser = isLikelyUser
        self.courtLabel = courtLabel
    }

    /// Human label for the UI, localized ("Player 1" / "Joueur 1"). Uses the
    /// in-app language via appLocalized so it follows the FR/EN switch.
    var displayName: String { appLocalized("Player %lld", index) }

    // CMTime isn't Codable by default; encode it as value/timescale like the
    // other models in CVMLModels.swift.
    enum CodingKeys: String, CodingKey {
        case id, index, positions, averagePosition, thumbnailFrameNumber
        case thumbnailTimeValue, thumbnailTimeTimescale
        case thumbnailBoundingBox, averageConfidence, isLikelyUser, courtLabel
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(UUID.self, forKey: .id)
        index = try c.decode(Int.self, forKey: .index)
        positions = try c.decode([CGPoint].self, forKey: .positions)
        averagePosition = try c.decode(CGPoint.self, forKey: .averagePosition)
        thumbnailFrameNumber = try c.decode(Int.self, forKey: .thumbnailFrameNumber)
        let v = try c.decode(Int64.self, forKey: .thumbnailTimeValue)
        let ts = try c.decode(Int32.self, forKey: .thumbnailTimeTimescale)
        thumbnailTime = CMTime(value: CMTimeValue(v), timescale: ts)
        thumbnailBoundingBox = try c.decode(CGRect.self, forKey: .thumbnailBoundingBox)
        averageConfidence = try c.decode(Float.self, forKey: .averageConfidence)
        isLikelyUser = try c.decode(Bool.self, forKey: .isLikelyUser)
        courtLabel = try c.decodeIfPresent(String.self, forKey: .courtLabel) ?? ""
    }

    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(id, forKey: .id)
        try c.encode(index, forKey: .index)
        try c.encode(positions, forKey: .positions)
        try c.encode(averagePosition, forKey: .averagePosition)
        try c.encode(thumbnailFrameNumber, forKey: .thumbnailFrameNumber)
        try c.encode(thumbnailTime.value, forKey: .thumbnailTimeValue)
        try c.encode(thumbnailTime.timescale, forKey: .thumbnailTimeTimescale)
        try c.encode(thumbnailBoundingBox, forKey: .thumbnailBoundingBox)
        try c.encode(averageConfidence, forKey: .averageConfidence)
        try c.encode(isLikelyUser, forKey: .isLikelyUser)
        try c.encode(courtLabel, forKey: .courtLabel)
    }
}

// MARK: - Player Identification Service

/// Turns raw player detections into a small ordered set of `PlayerCandidate`s.
///
/// Algorithm (deliberately simple and explainable):
///  1. Keep only `.player` detections.
///  2. Cluster them by average court position using a greedy nearest-centroid
///     pass with a distance threshold. Racket-sport players hold their side,
///     so position is a strong, cheap grouping signal within a clip.
///  3. For each cluster, choose the best detection (largest box × confidence)
///     as the thumbnail source, compute the average position and confidence.
///  4. Order clusters so the near-side (highest average `y`) player is index 1
///     and flagged `isLikelyUser`.
final class PlayerIdentification {

    /// Max distance (normalised, 0–1) between a detection's centre and a
    /// cluster centroid to join that cluster. ~0.18 of the frame: comfortably
    /// larger than a player's own jitter between frames, smaller than the gap
    /// between two players on opposite sides.
    private let clusterDistanceThreshold: CGFloat

    /// Clusters with fewer than this many detections are treated as noise
    /// (e.g. a referee walking through, a brief false positive) and dropped.
    private let minDetectionsPerCandidate: Int

    /// Safety cap: a court has at most 4 players (doubles). We never surface
    /// more than this many candidates, keeping the strongest ones.
    private let maxCandidates: Int

    /// Two clusters whose centroids are within this normalised distance are
    /// merged — they're almost certainly the same person the greedy pass split.
    /// Larger than `clusterDistanceThreshold` so a drifting player is re-joined
    /// but two genuinely separate players (who hold distinct court areas) are
    /// not. ~0.22 of the frame.
    private let mergeDistance: CGFloat

    /// A cluster is only kept if its detection count is at least this FRACTION
    /// of the biggest cluster's. A real player is tracked a comparable number of
    /// times across the clip; a stray false positive is seen far less. This is
    /// what lets singles return 2 players instead of a forced 4.
    private let minRelativeSupport: Double

    /// A player box smaller than this FRACTION of the median player-box area is
    /// treated as a background/adjacent-court player and dropped. Distant courts
    /// are far smaller due to perspective; the real far-side player in the SAME
    /// court stays comfortably above this. ~0.30 of the median.
    private let backgroundAreaFraction: CGFloat

    init(
        clusterDistanceThreshold: CGFloat = 0.18,
        minDetectionsPerCandidate: Int = 3,
        maxCandidates: Int = 4,
        mergeDistance: CGFloat = 0.22,
        minRelativeSupport: Double = 0.35,
        backgroundAreaFraction: CGFloat = 0.30
    ) {
        self.clusterDistanceThreshold = clusterDistanceThreshold
        self.minDetectionsPerCandidate = minDetectionsPerCandidate
        self.maxCandidates = maxCandidates
        self.mergeDistance = mergeDistance
        self.minRelativeSupport = minRelativeSupport
        self.backgroundAreaFraction = backgroundAreaFraction
    }

    /// Builds ordered player candidates from a full set of frame detections.
    /// - Parameter detections: all detections from the analysis (any class).
    /// - Returns: candidates ordered near-side first; empty if no players.
    func identifyPlayers(from detections: [Detection]) -> [PlayerCandidate] {
        var players = detections.filter { $0.objectClass == .player }
        guard !players.isEmpty else { return [] }

        // --- 0. Reject players on OTHER courts (background) ------------------
        // A person playing on an adjacent/background court appears far away:
        // their bounding box is much SMALLER than the real players' (perspective)
        // and sits high in the frame. We drop boxes whose area is well below the
        // median player-box area, which removes distant background players
        // without touching the real near/far pair (a far-side player in the
        // SAME court is still reasonably large).
        let areas = players.map { $0.boundingBox.width * $0.boundingBox.height }.sorted()
        let medianArea = areas[areas.count / 2]
        let minArea = medianArea * backgroundAreaFraction
        let filtered = players.filter { ($0.boundingBox.width * $0.boundingBox.height) >= minArea }
        // Only apply the filter if it keeps a sensible amount of data (guards
        // against a clip where everyone is genuinely small/far).
        if filtered.count >= max(minDetectionsPerCandidate, players.count / 3) {
            players = filtered
        }

        // --- 1. Split by COURT SIDE (depth), not free 2D position -----------
        // Players hold their own side of the net: in a racket sport they are
        // separated mainly in DEPTH (y: near camera vs far), while each one
        // roams freely LEFT–RIGHT on their own side as they play. Clustering in
        // free 2D therefore wrongly splits one laterally-moving player into two
        // ("Far Left" + "Far Right"). So we first separate players by y-band
        // (near vs far), and treat left–right motion as normal play, not a new
        // player. This matches the real case "one player in front of the other".
        let allY = players.map { $0.boundingBox.midY }.sorted()
        let splitY = allY[allY.count / 2]   // median depth = the net line, roughly

        let nearHalf = players.filter { $0.boundingBox.midY >= splitY }  // closer to camera
        let farHalf  = players.filter { $0.boundingBox.midY <  splitY }

        // --- 2. Within each half, decide 1 or 2 players ---------------------
        // One side holds one player (singles) or two (doubles). We look at the
        // left–right distribution on that side: if detections form two clearly
        // separated lateral groups, it's two players; otherwise one. A single
        // player roaming the whole width stays ONE player.
        var clusters: [[Detection]] = []
        clusters.append(contentsOf: splitHalfIntoPlayers(nearHalf))
        clusters.append(contentsOf: splitHalfIntoPlayers(farHalf))

        // --- 3. Drop noise, keep the strongest, cap at 4 -------------------
        var kept = clusters.filter { $0.count >= minDetectionsPerCandidate }
        if kept.isEmpty { kept = clusters }
        kept.sort { $0.count > $1.count }
        if let strongest = kept.first?.count {
            let relativeFloor = max(minDetectionsPerCandidate, Int(Double(strongest) * minRelativeSupport))
            kept = kept.filter { $0.count >= relativeFloor }
        }
        kept = Array(kept.prefix(maxCandidates))

        // --- 3. Build a candidate per cluster -------------------------------
        var provisional: [(avg: CGPoint, conf: Float, best: Detection, dets: [CGPoint])] = []
        for cluster in kept {
            let avgX = cluster.map { $0.boundingBox.midX }.reduce(0, +) / CGFloat(cluster.count)
            let avgY = cluster.map { $0.boundingBox.midY }.reduce(0, +) / CGFloat(cluster.count)
            let avgConf = cluster.map { $0.confidence }.reduce(0, +) / Float(cluster.count)

            // Best detection = largest box area weighted by confidence. A big,
            // confident box is the clearest frame to show as a thumbnail.
            let best = cluster.max { a, b in
                let areaA = a.boundingBox.width * a.boundingBox.height * CGFloat(a.confidence)
                let areaB = b.boundingBox.width * b.boundingBox.height * CGFloat(b.confidence)
                return areaA < areaB
            }!

            let sortedCluster = cluster.sorted { $0.frameNumber < $1.frameNumber }
            let positions = sortedCluster.map { CGPoint(x: $0.boundingBox.midX, y: $0.boundingBox.midY) }
            provisional.append((CGPoint(x: avgX, y: avgY), avgConf, best, positions))
        }

        // --- 4. Assign court labels (side × lane) and order them -------------
        // A racket court splits into a NEAR half (closer to the camera = higher
        // y) and a FAR half, each with a LEFT and RIGHT lane. Labelling by
        // side × lane makes the (up to) four doubles players distinguishable and
        // stable, instead of an opaque "Player 1..4". We split sides on the
        // MEDIAN y of the candidates so it adapts to how the clip is framed.
        guard !provisional.isEmpty else { return [] }

        let ys = provisional.map { $0.avg.y }.sorted()
        let medianY = ys[ys.count / 2]

        // near = y strictly greater than (or equal to) the median → closer to camera.
        func isNear(_ p: CGFloat) -> Bool { p >= medianY }

        // Order: near row first (left→right), then far row (left→right). This is
        // the natural reading order of a doubles court from the camera.
        let ordered = provisional.sorted { a, b in
            let aNear = isNear(a.avg.y), bNear = isNear(b.avg.y)
            if aNear != bNear { return aNear && !bNear }   // near row before far row
            return a.avg.x < b.avg.x                         // then left → right
        }

        // Count how many candidates ended up on each side so we only add a
        // left/right lane when it actually disambiguates two players on that
        // side. For "one in front of the other" (singles) each side has one
        // player and we label them simply "Near" / "Far".
        let nearCount = provisional.filter { isNear($0.avg.y) }.count
        let farCount = provisional.count - nearCount

        return ordered.enumerated().map { (i, p) in
            let near = isNear(p.avg.y)
            let side = near ? "Near" : "Far"
            let countOnSide = near ? nearCount : farCount
            let label: String
            if countOnSide >= 2 {
                label = "\(side) \(p.avg.x < 0.5 ? "Left" : "Right")"
            } else {
                label = side   // lone player on this side → no lane needed
            }
            return PlayerCandidate(
                index: i + 1,
                positions: p.dets,
                averagePosition: p.avg,
                thumbnailFrameNumber: p.best.frameNumber,
                thumbnailTime: p.best.timestamp,
                thumbnailBoundingBox: p.best.boundingBox,
                averageConfidence: p.conf,
                // Default to the first near-side player as the likely user.
                isLikelyUser: i == 0,
                courtLabel: label
            )
        }
    }

    /// Decides whether one court half holds ONE player or TWO, and returns the
    /// detections grouped accordingly.
    ///
    /// A single player roams the full width of their side, so wide left–right
    /// spread alone does NOT mean two players. We only split into two when the
    /// lateral positions form two groups with a clear EMPTY GAP between them AND
    /// both groups have enough support. Otherwise it's one player.
    private func splitHalfIntoPlayers(_ half: [Detection]) -> [[Detection]] {
        guard half.count >= minDetectionsPerCandidate else {
            return half.isEmpty ? [] : [half]
        }

        // Build a histogram of x positions (10 bins across the frame width).
        let bins = 10
        var counts = [Int](repeating: 0, count: bins)
        for d in half {
            let b = min(bins - 1, max(0, Int(d.boundingBox.midX * CGFloat(bins))))
            counts[b] += 1
        }

        // Find the largest EMPTY (or near-empty) gap between two populated
        // regions. Two players on the same side sit apart with a sparse middle;
        // one roaming player fills the middle too.
        let noiseFloor = max(1, half.count / (bins * 2))   // a bin is "empty" below this
        // Locate the first and last populated bins.
        guard let firstPop = counts.firstIndex(where: { $0 > noiseFloor }),
              let lastPop = counts.lastIndex(where: { $0 > noiseFloor }),
              lastPop > firstPop else {
            return [half]   // all mass in one place → one player
        }

        // Scan the interior for the longest run of empty bins.
        var bestGapStart = -1, bestGapLen = 0
        var runStart = -1, runLen = 0
        for b in (firstPop + 1)..<lastPop {
            if counts[b] <= noiseFloor {
                if runStart < 0 { runStart = b; runLen = 0 }
                runLen += 1
                if runLen > bestGapLen { bestGapLen = runLen; bestGapStart = runStart }
            } else {
                runStart = -1; runLen = 0
            }
        }

        // Require a clear gap (≥ 2 empty bins = 20% of width) to call it two
        // players; otherwise it's one roaming player.
        guard bestGapLen >= 2, bestGapStart > 0 else { return [half] }

        let splitBinCenter = CGFloat(bestGapStart) + CGFloat(bestGapLen) / 2.0
        let splitX = splitBinCenter / CGFloat(bins)

        let left = half.filter { $0.boundingBox.midX < splitX }
        let right = half.filter { $0.boundingBox.midX >= splitX }

        // Both sub-groups must have real support to count as two players.
        guard left.count >= minDetectionsPerCandidate,
              right.count >= minDetectionsPerCandidate else {
            return [half]
        }
        return [left, right]
    }
}
