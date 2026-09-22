//
//  FeatureExtractorTests.swift
//  nextmoveTests
//
//  Unit tests for FeatureExtractor ball trajectory analysis
//  Validates: Requirements 4.1-4.7
//

import XCTest
import AVFoundation
@testable import nextmove

final class FeatureExtractorTests: XCTestCase {
    
    var featureExtractor: FeatureExtractor!
    
    override func setUp() {
        super.setUp()
        featureExtractor = FeatureExtractor()
    }
    
    override func tearDown() {
        featureExtractor = nil
        super.tearDown()
    }
    
    // MARK: - Ball Trajectory Tests
    
    func testExtractBallTrajectories_WithValidBallTracks_ReturnsTrajectories() async throws {
        // Given: Ball tracks with sufficient data
        let ballTrack = createBallTrack(
            detections: [
                createDetection(x: 0.1, y: 0.2, frameNumber: 0, time: 0.0),
                createDetection(x: 0.3, y: 0.5, frameNumber: 1, time: 0.1),
                createDetection(x: 0.5, y: 0.8, frameNumber: 2, time: 0.2)
            ]
        )
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [ballTrack],
            sportType: .pickleball
        )
        
        // Then: Ball trajectories are extracted
        XCTAssertEqual(features.ballTrajectories.count, 1)
        XCTAssertEqual(features.ballTrajectories[0].track.id, ballTrack.id)
    }
    
    func testExtractBallTrajectories_WithNoBallTracks_ThrowsError() async {
        // Given: No ball tracks
        let playerTrack = createPlayerTrack()
        
        // When/Then: Should throw insufficient data error
        do {
            _ = try await featureExtractor.extractFeatures(
                from: [playerTrack],
                sportType: .pickleball
            )
            XCTFail("Expected error to be thrown")
        } catch let error as FeatureExtractionError {
            if case .insufficientData(let component) = error {
                XCTAssertEqual(component, "ball trajectories")
            } else {
                XCTFail("Wrong error type")
            }
        } catch {
            XCTFail("Wrong error type: \(error)")
        }
    }
    
    func testShotDirectionClassification_CrossCourt() async throws {
        // Given: Ball moving diagonally right (cross-court)
        let ballTrack = createBallTrack(
            detections: [
                createDetection(x: 0.2, y: 0.2, frameNumber: 0, time: 0.0),
                createDetection(x: 0.5, y: 0.5, frameNumber: 1, time: 0.1),
                createDetection(x: 0.8, y: 0.8, frameNumber: 2, time: 0.2)
            ]
        )
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [ballTrack],
            sportType: .pickleball
        )
        
        // Then: Direction is cross-court
        XCTAssertEqual(features.ballTrajectories[0].direction, .crossCourt)
    }
    
    func testShotDirectionClassification_DownTheLine() async throws {
        // Given: Ball moving left (down the line)
        let ballTrack = createBallTrack(
            detections: [
                createDetection(x: 0.8, y: 0.2, frameNumber: 0, time: 0.0),
                createDetection(x: 0.5, y: 0.5, frameNumber: 1, time: 0.1),
                createDetection(x: 0.2, y: 0.8, frameNumber: 2, time: 0.2)
            ]
        )
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [ballTrack],
            sportType: .pickleball
        )
        
        // Then: Direction is down the line
        XCTAssertEqual(features.ballTrajectories[0].direction, .downTheLine)
    }
    
    func testShotDirectionClassification_Middle() async throws {
        // Given: Ball moving mostly vertical (middle)
        let ballTrack = createBallTrack(
            detections: [
                createDetection(x: 0.5, y: 0.2, frameNumber: 0, time: 0.0),
                createDetection(x: 0.52, y: 0.5, frameNumber: 1, time: 0.1),
                createDetection(x: 0.51, y: 0.8, frameNumber: 2, time: 0.2)
            ]
        )
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [ballTrack],
            sportType: .pickleball
        )
        
        // Then: Direction is middle
        XCTAssertEqual(features.ballTrajectories[0].direction, .middle)
    }
    
    func testShotDepthEstimation_Kitchen() async throws {
        // Given: Ball ending near net (y >= 0.7)
        let ballTrack = createBallTrack(
            detections: [
                createDetection(x: 0.5, y: 0.2, frameNumber: 0, time: 0.0),
                createDetection(x: 0.5, y: 0.5, frameNumber: 1, time: 0.1),
                createDetection(x: 0.5, y: 0.85, frameNumber: 2, time: 0.2)
            ]
        )
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [ballTrack],
            sportType: .pickleball
        )
        
        // Then: Depth is kitchen
        XCTAssertEqual(features.ballTrajectories[0].depth, .kitchen)
    }
    
    func testShotDepthEstimation_MidCourt() async throws {
        // Given: Ball ending in mid-court (0.3 <= y < 0.7)
        let ballTrack = createBallTrack(
            detections: [
                createDetection(x: 0.5, y: 0.2, frameNumber: 0, time: 0.0),
                createDetection(x: 0.5, y: 0.4, frameNumber: 1, time: 0.1),
                createDetection(x: 0.5, y: 0.5, frameNumber: 2, time: 0.2)
            ]
        )
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [ballTrack],
            sportType: .pickleball
        )
        
        // Then: Depth is mid-court
        XCTAssertEqual(features.ballTrajectories[0].depth, .midCourt)
    }
    
    func testShotDepthEstimation_Baseline() async throws {
        // Given: Ball ending near baseline (y < 0.3)
        let ballTrack = createBallTrack(
            detections: [
                createDetection(x: 0.5, y: 0.5, frameNumber: 0, time: 0.0),
                createDetection(x: 0.5, y: 0.3, frameNumber: 1, time: 0.1),
                createDetection(x: 0.5, y: 0.15, frameNumber: 2, time: 0.2)
            ]
        )
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [ballTrack],
            sportType: .pickleball
        )
        
        // Then: Depth is baseline
        XCTAssertEqual(features.ballTrajectories[0].depth, .baseline)
    }
    
    func testBallSpeedCalculation_WithValidTrack_ReturnsSpeed() async throws {
        // Given: Ball track with position changes
        let ballTrack = createBallTrack(
            detections: [
                createDetection(x: 0.1, y: 0.1, frameNumber: 0, time: 0.0),
                createDetection(x: 0.3, y: 0.3, frameNumber: 1, time: 0.1),
                createDetection(x: 0.5, y: 0.5, frameNumber: 2, time: 0.2)
            ]
        )
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [ballTrack],
            sportType: .pickleball
        )
        
        // Then: Speed is calculated
        XCTAssertNotNil(features.ballTrajectories[0].estimatedSpeed)
        XCTAssertGreaterThan(features.ballTrajectories[0].estimatedSpeed!, 0.0)
    }
    
    func testBallSpeedCalculation_WithSingleDetection_ReturnsNil() async throws {
        // Given: Ball track with only one detection
        let ballTrack = createBallTrack(
            detections: [
                createDetection(x: 0.5, y: 0.5, frameNumber: 0, time: 0.0)
            ]
        )
        
        // When: Extracting features (should skip this track)
        let features = try await featureExtractor.extractFeatures(
            from: [ballTrack],
            sportType: .pickleball
        )
        
        // Then: No trajectories extracted (insufficient data)
        XCTAssertEqual(features.ballTrajectories.count, 0)
    }
    
    func testLowConfidenceMarking() async throws {
        // Given: Ball track with low confidence (< 0.5)
        let ballTrack = createBallTrack(
            detections: [
                createDetection(x: 0.1, y: 0.2, frameNumber: 0, time: 0.0, confidence: 0.3),
                createDetection(x: 0.3, y: 0.5, frameNumber: 1, time: 0.1, confidence: 0.4),
                createDetection(x: 0.5, y: 0.8, frameNumber: 2, time: 0.2, confidence: 0.35)
            ]
        )
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [ballTrack],
            sportType: .pickleball
        )
        
        // Then: Trajectory is marked with low confidence
        XCTAssertLessThan(features.ballTrajectories[0].confidence, 0.5)
    }
    
    func testRallyComputation_SingleRally() async throws {
        // Given: Ball tracks forming a single rally
        let ballTrack1 = createBallTrack(
            detections: [
                createDetection(x: 0.1, y: 0.2, frameNumber: 0, time: 0.0),
                createDetection(x: 0.3, y: 0.5, frameNumber: 1, time: 0.5)
            ]
        )
        let ballTrack2 = createBallTrack(
            detections: [
                createDetection(x: 0.5, y: 0.8, frameNumber: 2, time: 1.0),
                createDetection(x: 0.7, y: 0.6, frameNumber: 3, time: 1.5)
            ]
        )
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [ballTrack1, ballTrack2],
            sportType: .pickleball
        )
        
        // Then: One rally is computed
        XCTAssertEqual(features.rallies.count, 1)
        XCTAssertEqual(features.rallies[0].shotCount, 2)
    }
    
    func testRallyComputation_MultipleRallies() async throws {
        // Given: Ball tracks with gap > 3 seconds (separate rallies)
        let ballTrack1 = createBallTrack(
            detections: [
                createDetection(x: 0.1, y: 0.2, frameNumber: 0, time: 0.0),
                createDetection(x: 0.3, y: 0.5, frameNumber: 1, time: 0.5)
            ]
        )
        let ballTrack2 = createBallTrack(
            detections: [
                createDetection(x: 0.5, y: 0.8, frameNumber: 2, time: 5.0), // 4.5 second gap
                createDetection(x: 0.7, y: 0.6, frameNumber: 3, time: 5.5)
            ]
        )
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [ballTrack1, ballTrack2],
            sportType: .pickleball
        )
        
        // Then: Two rallies are computed
        XCTAssertEqual(features.rallies.count, 2)
    }
    
    // MARK: - Helper Methods
    
    private func createBallTrack(detections: [Detection]) -> Track {
        let startTime = detections.first?.timestamp ?? CMTime.zero
        let endTime = detections.last?.timestamp ?? CMTime.zero
        let avgConfidence = detections.map { $0.confidence }.reduce(0, +) / Float(max(detections.count, 1))
        
        return Track(
            objectClass: .ball,
            detections: detections,
            startTime: startTime,
            endTime: endTime,
            averageConfidence: avgConfidence
        )
    }
    
    private func createPlayerTrack() -> Track {
        let detection = createDetection(x: 0.5, y: 0.5, frameNumber: 0, time: 0.0)
        return Track(
            objectClass: .player,
            detections: [detection],
            startTime: CMTime.zero,
            endTime: CMTime(seconds: 1.0, preferredTimescale: 600),
            averageConfidence: 0.8
        )
    }
    
    private func createDetection(
        x: Double,
        y: Double,
        frameNumber: Int,
        time: Double,
        confidence: Float = 0.8
    ) -> Detection {
        return Detection(
            objectClass: .ball,
            boundingBox: CGRect(x: x - 0.025, y: y - 0.025, width: 0.05, height: 0.05),
            confidence: confidence,
            frameNumber: frameNumber,
            timestamp: CMTime(seconds: time, preferredTimescale: 600)
        )
    }

    // MARK: - Player Movement Tests (Requirements 5.1-5.8)
    
    func testExtractPlayerMovement_WithValidPlayerTracks_ReturnsMovement() async throws {
        // Given: Player tracks with sufficient data
        let playerTrack = createPlayerTrackWithPositions([
            (x: 0.3, y: 0.5, time: 0.0),
            (x: 0.4, y: 0.6, time: 0.5),
            (x: 0.5, y: 0.7, time: 1.0)
        ])
        let ballTrack = createBallTrack(detections: [
            createDetection(x: 0.5, y: 0.5, frameNumber: 0, time: 0.0),
            createDetection(x: 0.6, y: 0.6, frameNumber: 1, time: 0.5)
        ])
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [playerTrack, ballTrack],
            sportType: .pickleball
        )
        
        // Then: Player movement is extracted
        XCTAssertGreaterThan(features.playerMovement.positioningHistory.count, 0)
        XCTAssertGreaterThan(features.playerMovement.confidence, 0.0)
    }
    
    func testExtractPlayerMovement_WithNoPlayerTracks_ReturnsEmptyMovement() async throws {
        // Given: Only ball tracks, no player tracks
        let ballTrack = createBallTrack(detections: [
            createDetection(x: 0.5, y: 0.5, frameNumber: 0, time: 0.0),
            createDetection(x: 0.6, y: 0.6, frameNumber: 1, time: 0.5)
        ])
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [ballTrack],
            sportType: .pickleball
        )
        
        // Then: Player movement is empty
        XCTAssertEqual(features.playerMovement.positioningHistory.count, 0)
        XCTAssertEqual(features.playerMovement.confidence, 0.0)
    }
    
    func testCourtCoverageZones_3x3Grid() async throws {
        // Given: Player positions covering different zones
        let playerTrack = createPlayerTrackWithPositions([
            (x: 0.1, y: 0.1, time: 0.0),  // backLeft
            (x: 0.5, y: 0.5, time: 0.5),  // midCenter
            (x: 0.8, y: 0.8, time: 1.0)   // frontRight
        ])
        let ballTrack = createBallTrack(detections: [
            createDetection(x: 0.5, y: 0.5, frameNumber: 0, time: 0.0),
            createDetection(x: 0.6, y: 0.6, frameNumber: 1, time: 0.5)
        ])
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [playerTrack, ballTrack],
            sportType: .pickleball
        )
        
        // Then: Court coverage includes multiple zones
        XCTAssertGreaterThan(features.playerMovement.courtCoverage.zones.count, 0)
        
        // Verify zones sum to approximately 1.0 (100%)
        let totalCoverage = features.playerMovement.courtCoverage.zones.values.reduce(0.0, +)
        XCTAssertEqual(totalCoverage, 1.0, accuracy: 0.01)
    }
    
    func testLeftRightBalance_BalancedCoverage() async throws {
        // Given: Player positions balanced left and right
        let playerTrack = createPlayerTrackWithPositions([
            (x: 0.2, y: 0.5, time: 0.0),  // left
            (x: 0.8, y: 0.5, time: 0.5),  // right
            (x: 0.3, y: 0.6, time: 1.0),  // left
            (x: 0.7, y: 0.6, time: 1.5)   // right
        ])
        let ballTrack = createBallTrack(detections: [
            createDetection(x: 0.5, y: 0.5, frameNumber: 0, time: 0.0),
            createDetection(x: 0.6, y: 0.6, frameNumber: 1, time: 0.5)
        ])
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [playerTrack, ballTrack],
            sportType: .pickleball
        )
        
        // Then: Left-right balance is near 0.0 (balanced)
        XCTAssertEqual(features.playerMovement.courtCoverage.leftRightBalance, 0.0, accuracy: 0.2)
    }
    
    func testLeftRightBalance_RightBias() async throws {
        // Given: Player positions mostly on right side
        let playerTrack = createPlayerTrackWithPositions([
            (x: 0.7, y: 0.5, time: 0.0),
            (x: 0.8, y: 0.6, time: 0.5),
            (x: 0.9, y: 0.7, time: 1.0)
        ])
        let ballTrack = createBallTrack(detections: [
            createDetection(x: 0.5, y: 0.5, frameNumber: 0, time: 0.0),
            createDetection(x: 0.6, y: 0.6, frameNumber: 1, time: 0.5)
        ])
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [playerTrack, ballTrack],
            sportType: .pickleball
        )
        
        // Then: Left-right balance is positive (right bias)
        XCTAssertGreaterThan(features.playerMovement.courtCoverage.leftRightBalance, 0.5)
    }
    
    func testLeftRightBalance_LeftBias() async throws {
        // Given: Player positions mostly on left side
        let playerTrack = createPlayerTrackWithPositions([
            (x: 0.1, y: 0.5, time: 0.0),
            (x: 0.2, y: 0.6, time: 0.5),
            (x: 0.3, y: 0.7, time: 1.0)
        ])
        let ballTrack = createBallTrack(detections: [
            createDetection(x: 0.5, y: 0.5, frameNumber: 0, time: 0.0),
            createDetection(x: 0.6, y: 0.6, frameNumber: 1, time: 0.5)
        ])
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [playerTrack, ballTrack],
            sportType: .pickleball
        )
        
        // Then: Left-right balance is negative (left bias)
        XCTAssertLessThan(features.playerMovement.courtCoverage.leftRightBalance, -0.5)
    }
    
    func testKitchenLineProximity_NearKitchenLine() async throws {
        // Given: Player positions near kitchen line (y=0.7)
        let playerTrack = createPlayerTrackWithPositions([
            (x: 0.5, y: 0.65, time: 0.0),
            (x: 0.5, y: 0.70, time: 0.5),
            (x: 0.5, y: 0.75, time: 1.0)
        ])
        let ballTrack = createBallTrack(detections: [
            createDetection(x: 0.5, y: 0.5, frameNumber: 0, time: 0.0),
            createDetection(x: 0.6, y: 0.6, frameNumber: 1, time: 0.5)
        ])
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [playerTrack, ballTrack],
            sportType: .pickleball
        )
        
        // Then: Kitchen line proximity is small (close to line)
        XCTAssertLessThan(features.playerMovement.courtCoverage.kitchenLineProximity, 0.1)
    }
    
    func testKitchenLineProximity_FarFromKitchenLine() async throws {
        // Given: Player positions far from kitchen line
        let playerTrack = createPlayerTrackWithPositions([
            (x: 0.5, y: 0.1, time: 0.0),
            (x: 0.5, y: 0.2, time: 0.5),
            (x: 0.5, y: 0.3, time: 1.0)
        ])
        let ballTrack = createBallTrack(detections: [
            createDetection(x: 0.5, y: 0.5, frameNumber: 0, time: 0.0),
            createDetection(x: 0.6, y: 0.6, frameNumber: 1, time: 0.5)
        ])
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [playerTrack, ballTrack],
            sportType: .pickleball
        )
        
        // Then: Kitchen line proximity is large (far from line)
        XCTAssertGreaterThan(features.playerMovement.courtCoverage.kitchenLineProximity, 0.4)
    }
    
    func testBaselineProximity_NearBaseline() async throws {
        // Given: Player positions near baseline (y=0.0)
        let playerTrack = createPlayerTrackWithPositions([
            (x: 0.5, y: 0.05, time: 0.0),
            (x: 0.5, y: 0.10, time: 0.5),
            (x: 0.5, y: 0.15, time: 1.0)
        ])
        let ballTrack = createBallTrack(detections: [
            createDetection(x: 0.5, y: 0.5, frameNumber: 0, time: 0.0),
            createDetection(x: 0.6, y: 0.6, frameNumber: 1, time: 0.5)
        ])
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [playerTrack, ballTrack],
            sportType: .pickleball
        )
        
        // Then: Baseline proximity is small (close to baseline)
        XCTAssertLessThan(features.playerMovement.courtCoverage.baselineProximity, 0.2)
    }
    
    func testMovementSpeed_WithPositionChanges_ReturnsNonZeroSpeeds() async throws {
        // Given: Player moving across court
        let playerTrack = createPlayerTrackWithPositions([
            (x: 0.2, y: 0.3, time: 0.0),
            (x: 0.5, y: 0.5, time: 0.5),
            (x: 0.8, y: 0.7, time: 1.0)
        ])
        let ballTrack = createBallTrack(detections: [
            createDetection(x: 0.5, y: 0.5, frameNumber: 0, time: 0.0),
            createDetection(x: 0.6, y: 0.6, frameNumber: 1, time: 0.5)
        ])
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [playerTrack, ballTrack],
            sportType: .pickleball
        )
        
        // Then: Movement speeds are calculated
        XCTAssertGreaterThan(features.playerMovement.movementSpeed.count, 0)
        XCTAssertGreaterThan(features.playerMovement.movementSpeed[0], 0.0)
    }
    
    func testMovementSpeed_WithStaticPosition_ReturnsZeroSpeed() async throws {
        // Given: Player staying in same position
        let playerTrack = createPlayerTrackWithPositions([
            (x: 0.5, y: 0.5, time: 0.0),
            (x: 0.5, y: 0.5, time: 0.5),
            (x: 0.5, y: 0.5, time: 1.0)
        ])
        let ballTrack = createBallTrack(detections: [
            createDetection(x: 0.5, y: 0.5, frameNumber: 0, time: 0.0),
            createDetection(x: 0.6, y: 0.6, frameNumber: 1, time: 0.5)
        ])
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [playerTrack, ballTrack],
            sportType: .pickleball
        )
        
        // Then: Movement speeds are near zero
        XCTAssertGreaterThan(features.playerMovement.movementSpeed.count, 0)
        for speed in features.playerMovement.movementSpeed {
            XCTAssertEqual(speed, 0.0, accuracy: 0.01)
        }
    }
    
    func testRecoveryPositions_AfterMovement_IdentifiesRecovery() async throws {
        // Given: Player moving then stopping (recovery)
        let playerTrack = createPlayerTrackWithPositions([
            (x: 0.2, y: 0.3, time: 0.0),
            (x: 0.5, y: 0.5, time: 0.2),  // Fast movement
            (x: 0.8, y: 0.7, time: 0.4),  // Fast movement
            (x: 0.8, y: 0.7, time: 0.6),  // Stopped (recovery)
            (x: 0.8, y: 0.7, time: 0.8)   // Still stopped
        ])
        let ballTrack = createBallTrack(detections: [
            createDetection(x: 0.5, y: 0.5, frameNumber: 0, time: 0.0),
            createDetection(x: 0.6, y: 0.6, frameNumber: 1, time: 0.5)
        ])
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [playerTrack, ballTrack],
            sportType: .pickleball
        )
        
        // Then: Recovery positions are identified
        XCTAssertGreaterThan(features.playerMovement.recoveryPositions.count, 0)
    }
    
    func testPlayerMovementConfidence_WithHighConfidenceTracks_ReturnsHighConfidence() async throws {
        // Given: Player track with high confidence
        let playerTrack = createPlayerTrackWithPositions(
            [(x: 0.5, y: 0.5, time: 0.0), (x: 0.6, y: 0.6, time: 0.5)],
            confidence: 0.9
        )
        let ballTrack = createBallTrack(detections: [
            createDetection(x: 0.5, y: 0.5, frameNumber: 0, time: 0.0),
            createDetection(x: 0.6, y: 0.6, frameNumber: 1, time: 0.5)
        ])
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [playerTrack, ballTrack],
            sportType: .pickleball
        )
        
        // Then: Player movement confidence is high
        XCTAssertGreaterThan(features.playerMovement.confidence, 0.8)
    }
    
    func testPlayerMovementConfidence_WithLowConfidenceTracks_ReturnsLowConfidence() async throws {
        // Given: Player track with low confidence
        let playerTrack = createPlayerTrackWithPositions(
            [(x: 0.5, y: 0.5, time: 0.0), (x: 0.6, y: 0.6, time: 0.5)],
            confidence: 0.3
        )
        let ballTrack = createBallTrack(detections: [
            createDetection(x: 0.5, y: 0.5, frameNumber: 0, time: 0.0),
            createDetection(x: 0.6, y: 0.6, frameNumber: 1, time: 0.5)
        ])
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [playerTrack, ballTrack],
            sportType: .pickleball
        )
        
        // Then: Player movement confidence is low
        XCTAssertLessThan(features.playerMovement.confidence, 0.5)
    }
    
    func testOverallConfidence_IncludesPlayerMovement() async throws {
        // Given: Both ball and player tracks with different confidences
        let ballTrack = createBallTrack(detections: [
            createDetection(x: 0.5, y: 0.5, frameNumber: 0, time: 0.0, confidence: 0.9),
            createDetection(x: 0.6, y: 0.6, frameNumber: 1, time: 0.5, confidence: 0.9)
        ])
        let playerTrack = createPlayerTrackWithPositions(
            [(x: 0.5, y: 0.5, time: 0.0), (x: 0.6, y: 0.6, time: 0.5)],
            confidence: 0.5
        )
        
        // When: Extracting features
        let features = try await featureExtractor.extractFeatures(
            from: [ballTrack, playerTrack],
            sportType: .pickleball
        )
        
        // Then: Overall confidence is minimum of components (conservative)
        XCTAssertLessThanOrEqual(features.confidence, 0.5)
    }
    
    // MARK: - Helper Methods for Player Movement Tests
    
    private func createPlayerTrackWithPositions(
        _ positions: [(x: Double, y: Double, time: Double)],
        confidence: Float = 0.8
    ) -> Track {
        let detections = positions.enumerated().map { index, pos in
            Detection(
                objectClass: .player,
                boundingBox: CGRect(x: pos.x - 0.05, y: pos.y - 0.05, width: 0.1, height: 0.1),
                confidence: confidence,
                frameNumber: index,
                timestamp: CMTime(seconds: pos.time, preferredTimescale: 600)
            )
        }
        
        let startTime = detections.first?.timestamp ?? CMTime.zero
        let endTime = detections.last?.timestamp ?? CMTime.zero
        
        return Track(
            objectClass: .player,
            detections: detections,
            startTime: startTime,
            endTime: endTime,
            averageConfidence: confidence
        )
    }
}
