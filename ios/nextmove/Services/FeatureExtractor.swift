//
//  FeatureExtractor.swift
//  nextmove
//
//  Derives performance metrics from object tracks
//  Validates: Requirements 4.1-4.7, 5.1-5.8, 6.1-6.7, 7.1-7.6
//

import Foundation
import CoreGraphics
import AVFoundation

/// Extracts performance features from object tracks
class FeatureExtractor: FeatureExtractorProtocol {
    
    // MARK: - Main Extraction Method
    
    /// Extracts performance features from object tracks
    /// - Parameters:
    ///   - tracks: Array of object tracks from video analysis
    ///   - sportType: Sport type for sport-specific feature extraction
    /// - Returns: Performance features including trajectories, movement, contacts, and issues
    /// - Throws: FeatureExtractionError
    func extractFeatures(from tracks: [Track], sportType: SportType) async throws -> PerformanceFeatures {
        // Extract ball trajectories
        let ballTrajectories = try await extractBallTrajectories(from: tracks, sportType: sportType)
        
        // Extract player movement analysis
        let playerMovement = try await extractPlayerMovement(from: tracks, sportType: sportType)
        
        // Identify which player is the user (near-side = highest avg Y in frame,
        // i.e. closest to the camera filming from behind the user's baseline).
        let playerTracks = tracks.filter { $0.objectClass == .player }
        let nearSideY = identifyNearSidePlayerY(from: playerTracks)

        // Compute rallies from ball trajectories, attributed to the near-side player.
        let rallies = computeRallies(from: ballTrajectories, nearSidePlayerY: nearSideY)
        
        // Detect performance issues
        let issues = try await detectPerformanceIssues(
            playerMovement: playerMovement,
            ballTrajectories: ballTrajectories,
            rallies: rallies,
            sportType: sportType
        )
        
        // Contact points - simplified for POC (empty for now)
        let contactPoints: [ContactPoint] = []
        
        // Compute overall confidence
        let confidence = computeOverallConfidence(
            ballTrajectories: ballTrajectories,
            playerMovement: playerMovement
        )
        
        return PerformanceFeatures(
            ballTrajectories: ballTrajectories,
            playerMovement: playerMovement,
            contactPoints: contactPoints,
            rallies: rallies,
            issues: issues,
            confidence: confidence
        )
    }
    
    // MARK: - Ball Trajectory Analysis (Requirements 4.1-4.7)
    
    /// Extracts ball trajectories from ball tracks
    /// Validates: Requirements 4.1-4.7
    private func extractBallTrajectories(from tracks: [Track], sportType: SportType) async throws -> [BallTrajectory] {
        let ballTracks = tracks.filter { $0.objectClass == .ball }
        
        guard !ballTracks.isEmpty else {
            throw FeatureExtractionError.insufficientData(component: "ball trajectories")
        }
        
        var trajectories: [BallTrajectory] = []
        
        for track in ballTracks {
            // Requirement 4.1: Compute ball trajectory path (already in Track.trajectory)
            let trajectory = track.trajectory
            
            guard trajectory.count >= 2 else {
                // Skip tracks with insufficient data
                continue
            }
            
            // Requirement 4.2: Identify shot direction
            let direction = classifyShotDirection(trajectory: trajectory)
            
            // Requirement 4.3: Estimate shot depth
            let depth = estimateShotDepth(trajectory: trajectory)
            
            // Requirement 4.4: Estimate ball speed
            let speed = calculateBallSpeed(track: track)
            
            // Requirement 4.6: Mark low-confidence trajectories (< 0.5)
            let confidence = track.averageConfidence
            
            let ballTrajectory = BallTrajectory(
                track: track,
                direction: direction,
                depth: depth,
                estimatedSpeed: speed,
                confidence: confidence
            )
            
            trajectories.append(ballTrajectory)
        }
        
        return trajectories
    }
    
    /// Classifies shot direction based on trajectory
    /// Validates: Requirement 4.2
    private func classifyShotDirection(trajectory: [CGPoint]) -> ShotDirection {
        guard trajectory.count >= 2 else {
            return .middle
        }
        
        let startPoint = trajectory.first!
        let endPoint = trajectory.last!
        
        // Calculate horizontal movement
        let horizontalDelta = endPoint.x - startPoint.x
        let verticalDelta = abs(endPoint.y - startPoint.y)
        
        // Determine direction based on horizontal movement relative to vertical
        let horizontalRatio = abs(horizontalDelta) / max(verticalDelta, 0.01)
        
        if horizontalRatio < 0.3 {
            // Mostly vertical movement
            return .middle
        } else if horizontalDelta > 0 {
            // Moving right (cross-court from left side)
            return .crossCourt
        } else {
            // Moving left (down the line from right side)
            return .downTheLine
        }
    }
    
    /// Estimates shot depth based on trajectory endpoint
    /// Validates: Requirement 4.3
    private func estimateShotDepth(trajectory: [CGPoint]) -> ShotDepth {
        guard let endPoint = trajectory.last else {
            return .midCourt
        }
        
        // Normalize y-coordinate (0.0 = baseline, 1.0 = net)
        let normalizedY = endPoint.y
        
        // Classify depth based on court zones
        // Kitchen: 0.7-1.0 (near net)
        // Mid-court: 0.3-0.7
        // Baseline: 0.0-0.3 (near baseline)
        
        if normalizedY >= 0.7 {
            return .kitchen
        } else if normalizedY >= 0.3 {
            return .midCourt
        } else {
            return .baseline
        }
    }
    
    /// Calculates ball speed from position deltas and timestamps
    /// Validates: Requirement 4.4
    private func calculateBallSpeed(track: Track) -> Double? {
        guard track.detections.count >= 2 else {
            return nil
        }
        
        var totalSpeed: Double = 0.0
        var speedCount = 0
        
        // Calculate speed between consecutive detections
        for i in 0..<(track.detections.count - 1) {
            let detection1 = track.detections[i]
            let detection2 = track.detections[i + 1]
            
            // Calculate distance (in normalized coordinates)
            let dx = detection2.boundingBox.midX - detection1.boundingBox.midX
            let dy = detection2.boundingBox.midY - detection1.boundingBox.midY
            let distance = sqrt(dx * dx + dy * dy)
            
            // Calculate time delta
            let timeDelta = detection2.timestamp.seconds - detection1.timestamp.seconds
            
            guard timeDelta > 0 else {
                continue
            }
            
            // Speed in normalized units per second
            let speed = distance / timeDelta
            totalSpeed += speed
            speedCount += 1
        }
        
        guard speedCount > 0 else {
            return nil
        }
        
        return totalSpeed / Double(speedCount)
    }
    
    /// Computes rally information from ball trajectories
    /// Validates: Requirement 4.7
    /// A single ball observation on a unified timeline (flattened across all
    /// ball tracks). This is the real signal used to segment rallies and count
    /// shots — independent of how the tracker happened to split the ball into
    /// tracks.
    private struct BallSample {
        let time: Double   // seconds
        let y: Double      // vertical position of the ball centroid (0–1)
        let conf: Float
    }

    /// Rally / shot detection from actual ball motion.
    ///
    /// Previous implementation counted one "rally" per ball TRACK and one "shot"
    /// per track — so a game the tracker stitched into 1–2 long ball tracks
    /// reported 1–2 rallies with 1–2 shots, regardless of the real play. That's
    /// what produced "0–2 rallies" on a full game.
    ///
    /// This version works off the ball's real trajectory:
    ///  1. Flatten every ball detection from every track into one timeline,
    ///     sorted by timestamp.
    ///  2. Segment RALLIES on gaps in ball activity: if the ball isn't seen for
    ///     longer than `rallyGapSeconds`, the point is dead and a new rally
    ///     starts.
    ///  3. Count SHOTS within a rally by vertical direction reversals: each time
    ///     the ball clearly changes vertical direction (a player sent it back),
    ///     that's another shot. A small displacement threshold ignores jitter.
    /// Returns the average Y position of the near-side player (the user), defined
    /// as the player whose detections have the highest mean Y coordinate in the frame
    /// (Y increases downward, so high Y = bottom of frame = near camera = user's side).
    /// Falls back to 0.75 (bottom quarter) if no player tracks are available.
    private func identifyNearSidePlayerY(from playerTracks: [Track]) -> Double {
        guard !playerTracks.isEmpty else { return 0.75 }

        // Average Y per track, then pick the track with the highest mean Y.
        let trackAverageYs: [Double] = playerTracks.map { track in
            let ys = track.detections.map { Double($0.boundingBox.midY) }
            return ys.isEmpty ? 0.0 : ys.reduce(0, +) / Double(ys.count)
        }
        return trackAverageYs.max() ?? 0.75
    }

    private func computeRallies(from trajectories: [BallTrajectory], nearSidePlayerY: Double) -> [Rally] {
        // Maximum plausible shots in a single pickleball/padel rally. Pro
        // rallies rarely exceed ~15 exchanges; the cap guards against any
        // residual noise. Shots are now counted as true net crossings
        // (see countShots), so this should rarely bind.
        let maxShotsPerRally = 20

        // (Net line for both segmentation AND point attribution is `netY`,
        // computed below from the ball's own vertical range — more reliable than
        // a player-derived midline.)

        // 1) Flatten all ball detections into one time-sorted timeline.
        var samples: [BallSample] = []
        for traj in trajectories {
            for det in traj.track.detections {
                samples.append(BallSample(
                    time: det.timestamp.seconds,
                    y: Double(det.boundingBox.midY),
                    conf: det.confidence
                ))
            }
        }
        guard !samples.isEmpty else { return [] }
        samples.sort { $0.time < $1.time }

        // Net line = MIDPOINT of the ball's vertical range (robust 5th/95th
        // percentiles). Declared BEFORE `flush` so the closure can capture it.
        let sortedY = samples.map { $0.y }.sorted()
        let lo = sortedY[max(0, Int(Double(sortedY.count) * 0.05))]
        let hi = sortedY[min(sortedY.count - 1, Int(Double(sortedY.count) * 0.95))]
        let netY = (lo + hi) / 2.0
        // Hysteresis band: the ball must be clearly past the net to count as a
        // side, so jitter at the net doesn't create phantom crossings. Widened
        // to 0.10 after calibration against a reference clip (long dinking
        // exchanges near the net were producing phantom crossings → over-split).
        let netBand = 0.10

        // 2) Segment into rallies by net-crossing rhythm (see below).
        var rallies: [Rally] = []
        var segment: [BallSample] = [samples[0]]

        func flush(_ seg: [BallSample]) {
            guard let first = seg.first, let last = seg.last else { return }
            // A real rally must contain an actual exchange: the ball has to have
            // been on BOTH sides of the net within the segment. A pure dead-ball
            // dwell (all on one side) is not a rally — this is what prevents the
            // trailing/standalone dwell from being miscounted as an extra point.
            let wasFar = seg.contains { $0.y < netY - netBand }
            let wasNear = seg.contains { $0.y > netY + netBand }
            guard wasFar && wasNear else { return }

            let rawShots = countShots(in: seg, netY: netY)
            let shots = min(rawShots, maxShotsPerRally)
            guard shots >= 1 else { return }

            // Point attribution (spatial heuristic). Use the SAME self-calibrated
            // net line `netY` as the segmentation — NOT the player-derived
            // `courtMidY`, which was often mis-placed so that nearly every rally
            // ended "on the far side" and got labelled a winner (that's why
            // Points gagnés ≈ Échanges). With `netY` the split is balanced:
            //   • ball ends on the FAR side (y < netY) → won on opponent's court
            //   • ball ends on the NEAR side (y ≥ netY) → point lost to our side
            // This is still a heuristic — it can't truly know who won a point
            // (that needs fault/score detection) — but it no longer labels
            // almost everything a winner.
            let outcome: RallyOutcome = last.y < netY ? .winner : .error

            rallies.append(Rally(
                startTime: CMTime(seconds: first.time, preferredTimescale: 600),
                endTime: CMTime(seconds: last.time, preferredTimescale: 600),
                shotCount: shots,
                outcome: outcome
            ))
        }

        // Rally segmentation.
        //
        // The ball is detected almost every frame (no detection gaps), so we
        // CANNOT split points on silence. Instead we split on the natural rhythm
        // of play: a point is alive while the ball keeps CROSSING THE NET; it is
        // over when the ball DWELLS on one side of the net for a while (dead
        // ball, pickup, server holding it before the next serve). So we end a
        // rally when the ball has stayed on the same side of `courtMidY` for
        // longer than `deadBallSeconds` without crossing back.
        // A point is alive while the ball keeps CROSSING THE NET; it's over when
        // the ball DWELLS on one side for longer than `deadBallSeconds` (dead
        // ball / pickup / server holding before the next serve). netY/netBand
        // are computed above (before `flush`).
        // 3.5s: calibrated against a reference clip (13 real
        // rallies). Shorter values (2.0–3.0s) split single points that had a
        // mid-rally lull, over-counting (20 then 17 rallies). 3.5s only breaks
        // on genuine dead-ball pauses between points, landing near the true
        // count. Tune here if rally counts drift from reality on other clips.
        let deadBallSeconds = 3.5

        // Side with deadband: returns +1 (far) / -1 (near) only when clearly on
        // a side, 0 while inside the net band (ambiguous).
        func sideOf(_ y: Double) -> Int {
            if y < netY - netBand { return 1 }
            if y > netY + netBand { return -1 }
            return 0
        }

        var lastCrossTime = samples[0].time       // last time the ball clearly crossed
        var currentSide = sideOf(samples[0].y)

        for i in 1..<samples.count {
            let s = samples[i]
            let side = sideOf(s.y)

            if side != 0 && side != currentSide && currentSide != 0 {
                // Ball clearly moved from one side to the other → a net crossing,
                // i.e. the exchange is still alive.
                currentSide = side
                lastCrossTime = s.time
                segment.append(s)
            } else {
                if side != 0 { currentSide = side }   // update side when definite
                // Dwell check: ball hasn't crossed the net for too long → dead
                // ball → close the point and open a new one.
                if s.time - lastCrossTime > deadBallSeconds {
                    flush(segment)
                    segment = [s]
                    lastCrossTime = s.time
                } else {
                    segment.append(s)
                }
            }
        }
        flush(segment)
        return rallies
    }

    /// Counts shots in a rally segment by vertical direction reversals of the
    /// ball. In a net sport the ball travels toward one player, gets returned,
    /// Counts shots in a rally as the number of times the ball CLEARLY CROSSES
    /// THE NET (one side to the other). A shot sends the ball across to the
    /// opponent, so net crossings ≈ shots. This is robust: a wide hysteresis
    /// band around the net means small jitter / dinking wobble near the net does
    /// NOT register as a shot (the old version counted tiny vertical reversals,
    /// which inflated long exchanges up to the 30-shot cap). Shots = crossings
    /// + 1 (the opening shot that put the ball in play).
    private func countShots(in samples: [BallSample], netY: Double) -> Int {
        guard samples.count >= 2 else { return samples.isEmpty ? 0 : 1 }

        // A shot must send the ball clearly past the net. Band of 0.12 ignores
        // near-net dinks that don't actually cross.
        let shotBand = 0.12
        func side(_ y: Double) -> Int {
            if y < netY - shotBand { return 1 }   // far
            if y > netY + shotBand { return -1 }  // near
            return 0                               // ambiguous (near the net)
        }

        var crossings = 0
        var cur = 0
        for s in samples {
            let sd = side(s.y)
            if sd != 0 {
                if cur != 0 && sd != cur { crossings += 1 }
                cur = sd
            }
        }
        return crossings + 1
    }

    
    
    // MARK: - Player Movement Analysis (Requirements 5.1-5.8)
    
    /// Extracts player movement patterns from player tracks
    /// Validates: Requirements 5.1-5.8
    private func extractPlayerMovement(from tracks: [Track], sportType: SportType) async throws -> PlayerMovement {
        let playerTracks = tracks.filter { $0.objectClass == .player }
        
        guard !playerTracks.isEmpty else {
            // Return empty movement data if no player tracks
            return createPlaceholderPlayerMovement()
        }
        
        // Convert player tracks to court positions
        let positioningHistory = extractPositioningHistory(from: playerTracks)
        
        guard !positioningHistory.isEmpty else {
            return createPlaceholderPlayerMovement()
        }
        
        // Requirement 5.1: Compute court coverage zones (3x3 grid)
        let courtCoverage = computeCourtCoverage(from: positioningHistory)
        
        // Requirement 5.4: Compute movement speed from position deltas
        let movementSpeed = calculateMovementSpeed(from: positioningHistory)
        
        // Requirement 5.5: Identify recovery positions (position after shot contact)
        let recoveryPositions = identifyRecoveryPositions(from: positioningHistory)
        
        // Compute confidence from player track quality
        let confidence = computePlayerMovementConfidence(from: playerTracks)
        
        return PlayerMovement(
            courtCoverage: courtCoverage,
            movementSpeed: movementSpeed,
            positioningHistory: positioningHistory,
            recoveryPositions: recoveryPositions,
            confidence: confidence
        )
    }
    
    /// Extracts positioning history from player tracks
    private func extractPositioningHistory(from playerTracks: [Track]) -> [CourtPosition] {
        var positions: [CourtPosition] = []
        
        for track in playerTracks {
            for detection in track.detections {
                let position = CourtPosition(
                    x: Double(detection.boundingBox.midX),
                    y: Double(detection.boundingBox.midY),
                    timestamp: detection.timestamp
                )
                positions.append(position)
            }
        }
        
        // Sort by timestamp
        return positions.sorted { $0.timestamp.seconds < $1.timestamp.seconds }
    }
    
    /// Computes court coverage metrics including zone distribution and balance
    /// Validates: Requirements 5.1, 5.2, 5.3, 5.7
    private func computeCourtCoverage(from positions: [CourtPosition]) -> CourtCoverage {
        guard !positions.isEmpty else {
            return CourtCoverage(
                zones: [:],
                leftRightBalance: 0.0,
                kitchenLineProximity: 0.0,
                baselineProximity: 0.0
            )
        }
        
        // Divide court into 3x3 grid and count time in each zone
        var zoneCounts: [CourtZone: Int] = [:]
        var leftCount = 0
        var rightCount = 0
        var kitchenLineDistances: [Double] = []
        var baselineDistances: [Double] = []
        
        for position in positions {
            // Classify position into zone
            let zone = classifyCourtZone(position: position)
            zoneCounts[zone, default: 0] += 1
            
            // Count left vs right for balance
            if position.x < 0.5 {
                leftCount += 1
            } else {
                rightCount += 1
            }
            
            // Requirement 5.2: Kitchen line proximity (kitchen line at y=0.7)
            let kitchenLineDistance = abs(position.y - 0.7)
            kitchenLineDistances.append(kitchenLineDistance)
            
            // Requirement 5.3: Baseline proximity (baseline at y=0.0)
            let baselineDistance = position.y
            baselineDistances.append(baselineDistance)
        }
        
        // Convert counts to percentages
        let totalCount = positions.count
        var zonePercentages: [CourtZone: Double] = [:]
        for (zone, count) in zoneCounts {
            zonePercentages[zone] = Double(count) / Double(totalCount)
        }
        
        // Requirement 5.7: Calculate left-right balance (-1.0 to 1.0)
        let totalSides = leftCount + rightCount
        let leftRightBalance = totalSides > 0 
            ? (Double(rightCount) - Double(leftCount)) / Double(totalSides)
            : 0.0
        
        // Average distances
        let avgKitchenLineProximity = kitchenLineDistances.reduce(0.0, +) / Double(kitchenLineDistances.count)
        let avgBaselineProximity = baselineDistances.reduce(0.0, +) / Double(baselineDistances.count)
        
        return CourtCoverage(
            zones: zonePercentages,
            leftRightBalance: leftRightBalance,
            kitchenLineProximity: avgKitchenLineProximity,
            baselineProximity: avgBaselineProximity
        )
    }
    
    /// Classifies a court position into one of 9 zones (3x3 grid)
    /// Validates: Requirement 5.1
    private func classifyCourtZone(position: CourtPosition) -> CourtZone {
        // Divide court into thirds horizontally and vertically
        // X: 0.0-0.33 (left), 0.33-0.67 (center), 0.67-1.0 (right)
        // Y: 0.0-0.33 (back), 0.33-0.67 (mid), 0.67-1.0 (front)
        
        let xZone: String
        if position.x < 0.33 {
            xZone = "Left"
        } else if position.x < 0.67 {
            xZone = "Center"
        } else {
            xZone = "Right"
        }
        
        let yZone: String
        if position.y < 0.33 {
            yZone = "back"
        } else if position.y < 0.67 {
            yZone = "mid"
        } else {
            yZone = "front"
        }
        
        let zoneName = yZone + xZone
        return CourtZone(rawValue: zoneName) ?? .midCenter
    }
    
    /// Calculates movement speed from position deltas
    /// Validates: Requirement 5.4
    private func calculateMovementSpeed(from positions: [CourtPosition]) -> [Double] {
        guard positions.count >= 2 else {
            return []
        }
        
        var speeds: [Double] = []
        
        for i in 0..<(positions.count - 1) {
            let pos1 = positions[i]
            let pos2 = positions[i + 1]
            
            // Calculate distance
            let dx = pos2.x - pos1.x
            let dy = pos2.y - pos1.y
            let distance = sqrt(dx * dx + dy * dy)
            
            // Calculate time delta
            let timeDelta = pos2.timestamp.seconds - pos1.timestamp.seconds
            
            guard timeDelta > 0 else {
                continue
            }
            
            // Speed in normalized units per second
            let speed = distance / timeDelta
            speeds.append(speed)
        }
        
        return speeds
    }
    
    /// Identifies recovery positions after shots
    /// Validates: Requirement 5.5
    private func identifyRecoveryPositions(from positions: [CourtPosition]) -> [CourtPosition] {
        // Recovery positions are positions where player stabilizes after movement
        // We identify these as positions where speed drops significantly
        
        guard positions.count >= 3 else {
            return []
        }
        
        var recoveryPositions: [CourtPosition] = []
        let speeds = calculateMovementSpeed(from: positions)
        
        guard !speeds.isEmpty else {
            return []
        }
        
        // Calculate average speed for threshold
        let avgSpeed = speeds.reduce(0.0, +) / Double(speeds.count)
        let recoveryThreshold = avgSpeed * 0.3 // 30% of average speed
        
        // Find positions where speed drops below threshold after being above it
        var wasMoving = false
        
        for i in 0..<speeds.count {
            let speed = speeds[i]
            
            if speed > avgSpeed {
                wasMoving = true
            } else if wasMoving && speed < recoveryThreshold {
                // Player has stopped after moving - this is a recovery position
                if i + 1 < positions.count {
                    recoveryPositions.append(positions[i + 1])
                }
                wasMoving = false
            }
        }
        
        return recoveryPositions
    }
    
    /// Computes confidence score for player movement analysis
    private func computePlayerMovementConfidence(from playerTracks: [Track]) -> Float {
        guard !playerTracks.isEmpty else {
            return 0.0
        }
        
        // Average confidence from all player tracks
        let totalConfidence = playerTracks.reduce(0.0) { $0 + $1.averageConfidence }
        return totalConfidence / Float(playerTracks.count)
    }
    
    // MARK: - Placeholder Methods
    
    /// Creates placeholder player movement data
    private func createPlaceholderPlayerMovement() -> PlayerMovement {
        let emptyCoverage = CourtCoverage(
            zones: [:],
            leftRightBalance: 0.0,
            kitchenLineProximity: 0.0,
            baselineProximity: 0.0
        )
        
        return PlayerMovement(
            courtCoverage: emptyCoverage,
            movementSpeed: [],
            positioningHistory: [],
            recoveryPositions: [],
            confidence: 0.0
        )
    }
    
    /// Computes overall confidence from component confidences
    private func computeOverallConfidence(
        ballTrajectories: [BallTrajectory],
        playerMovement: PlayerMovement
    ) -> Float {
        var confidences: [Float] = []
        
        // Add ball trajectory confidence
        if !ballTrajectories.isEmpty {
            let ballConfidence = ballTrajectories.reduce(0.0) { $0 + $1.confidence } / Float(ballTrajectories.count)
            confidences.append(ballConfidence)
        }
        
        // Add player movement confidence
        if playerMovement.confidence > 0.0 {
            confidences.append(playerMovement.confidence)
        }
        
        guard !confidences.isEmpty else {
            return 0.0
        }
        
        // Return minimum confidence (most conservative)
        return confidences.min() ?? 0.0
    }
    
    // MARK: - Performance Issue Detection (Requirements 7.1-7.6)
    
    /// Detects performance issues from extracted features
    /// Validates: Requirements 7.1-7.6
    private func detectPerformanceIssues(
        playerMovement: PlayerMovement,
        ballTrajectories: [BallTrajectory],
        rallies: [Rally],
        sportType: SportType
    ) async throws -> [PerformanceIssue] {
        var issues: [PerformanceIssue] = []
        
        // Requirement 7.1: Static positioning detection
        if let staticIssue = detectStaticPositioning(playerMovement: playerMovement, rallies: rallies) {
            issues.append(staticIssue)
        }
        
        // Requirement 7.2: Depth positioning detection
        if let depthIssue = detectDepthPositioning(playerMovement: playerMovement) {
            issues.append(depthIssue)
        }
        
        // Requirement 7.4: Coverage imbalance detection
        if let coverageIssue = detectCoverageImbalance(playerMovement: playerMovement) {
            issues.append(coverageIssue)
        }
        
        // Requirement 7.6: Recovery positioning detection
        if let recoveryIssue = detectRecoveryPositioning(playerMovement: playerMovement, rallies: rallies) {
            issues.append(recoveryIssue)
        }
        
        return issues
    }
    
    /// Detects static positioning issue (staying in same zone too long)
    /// Validates: Requirement 7.1
    private func detectStaticPositioning(playerMovement: PlayerMovement, rallies: [Rally]) -> PerformanceIssue? {
        let positions = playerMovement.positioningHistory
        
        guard positions.count >= 10 else {
            return nil
        }
        
        // Check for extended periods in the same zone during rallies
        var staticOccurrences = 0
        var currentZone: CourtZone?
        var zoneStartTime: CMTime?
        
        for position in positions {
            let zone = classifyCourtZone(position: position)
            
            if zone == currentZone {
                // Still in same zone - check duration
                if let startTime = zoneStartTime {
                    let duration = position.timestamp.seconds - startTime.seconds
                    if duration > 5.0 {
                        staticOccurrences += 1
                        // Reset to avoid double counting
                        zoneStartTime = position.timestamp
                    }
                }
            } else {
                // Moved to new zone
                currentZone = zone
                zoneStartTime = position.timestamp
            }
        }
        
        guard staticOccurrences > 0 else {
            return nil
        }
        
        // Compute severity based on frequency
        let severity = min(Float(staticOccurrences) / 10.0, 1.0)
        
        return PerformanceIssue(
            type: .staticPositioning,
            severity: severity,
            occurrences: staticOccurrences,
            description: "Staying in the same court position for extended periods",
            confidence: playerMovement.confidence
        )
    }
    
    /// Detects depth positioning issue (too far from kitchen line)
    /// Validates: Requirement 7.2
    private func detectDepthPositioning(playerMovement: PlayerMovement) -> PerformanceIssue? {
        let kitchenLineProximity = playerMovement.courtCoverage.kitchenLineProximity
        
        // Threshold: average distance > 0.3 (30% of court depth)
        guard kitchenLineProximity > 0.3 else {
            return nil
        }
        
        // Compute severity based on distance
        let severity = min(Float(kitchenLineProximity), 1.0)
        
        // Count occurrences (positions far from kitchen line)
        let farPositions = playerMovement.positioningHistory.filter { position in
            abs(position.y - 0.7) > 0.3
        }
        
        return PerformanceIssue(
            type: .depthPositioning,
            severity: severity,
            occurrences: farPositions.count,
            description: "Playing too far from the kitchen line",
            confidence: playerMovement.confidence
        )
    }
    
    /// Detects coverage imbalance issue (favoring one side)
    /// Validates: Requirement 7.4
    private func detectCoverageImbalance(playerMovement: PlayerMovement) -> PerformanceIssue? {
        let balance = abs(playerMovement.courtCoverage.leftRightBalance)
        
        // Threshold: imbalance > 0.3 (30% asymmetry)
        guard balance > 0.3 else {
            return nil
        }
        
        // Compute severity based on imbalance magnitude
        let severity = min(Float(balance), 1.0)
        
        // Determine which side is favored
        let favoredSide = playerMovement.courtCoverage.leftRightBalance > 0 ? "right" : "left"
        
        return PerformanceIssue(
            type: .coverageImbalance,
            severity: severity,
            occurrences: 1,
            description: "Favoring the \(favoredSide) side of the court",
            confidence: playerMovement.confidence
        )
    }
    
    /// Detects recovery positioning issue (not returning to center)
    /// Validates: Requirement 7.6
    private func detectRecoveryPositioning(playerMovement: PlayerMovement, rallies: [Rally]) -> PerformanceIssue? {
        let recoveryPositions = playerMovement.recoveryPositions
        
        // Need at least 5 recovery positions to assess pattern
        guard recoveryPositions.count >= 5 else {
            return nil
        }
        
        // Check how many recovery positions are near center (x: 0.4-0.6)
        let centerRecoveries = recoveryPositions.filter { position in
            position.x >= 0.4 && position.x <= 0.6
        }
        
        let centerRecoveryRate = Double(centerRecoveries.count) / Double(recoveryPositions.count)
        
        // Threshold: < 50% of recoveries are to center
        guard centerRecoveryRate < 0.5 else {
            return nil
        }
        
        // Compute severity based on how far from ideal
        let severity = Float(1.0 - centerRecoveryRate)
        
        let poorRecoveries = recoveryPositions.count - centerRecoveries.count
        
        return PerformanceIssue(
            type: .recoveryPositioning,
            severity: severity,
            occurrences: poorRecoveries,
            description: "Not returning to center court position after shots",
            confidence: playerMovement.confidence
        )
    }
}
