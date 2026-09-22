//
//  CVMLModelsTests.swift
//  nextmoveTests
//
//  Unit tests for CV/ML data models
//

import XCTest
import CoreGraphics
import AVFoundation
@testable import nextmove

final class CVMLModelsTests: XCTestCase {
    
    // MARK: - ObjectClass Tests
    
    func testObjectClassRawValues() {
        XCTAssertEqual(ObjectClass.ball.rawValue, "ball")
        XCTAssertEqual(ObjectClass.player.rawValue, "player")
        XCTAssertEqual(ObjectClass.paddle.rawValue, "paddle")
        XCTAssertEqual(ObjectClass.courtLine.rawValue, "courtLine")
        XCTAssertEqual(ObjectClass.net.rawValue, "net")
        XCTAssertEqual(ObjectClass.netPost.rawValue, "netPost")
    }
    
    func testObjectClassCodable() throws {
        let objectClass = ObjectClass.ball
        let encoded = try JSONEncoder().encode(objectClass)
        let decoded = try JSONDecoder().decode(ObjectClass.self, from: encoded)
        XCTAssertEqual(decoded, objectClass)
    }
    
    // MARK: - Detection Tests
    
    func testDetectionInitialization() {
        let timestamp = CMTime(seconds: 1.5, preferredTimescale: 600)
        let boundingBox = CGRect(x: 0.1, y: 0.2, width: 0.3, height: 0.4)
        
        let detection = Detection(
            objectClass: .ball,
            boundingBox: boundingBox,
            confidence: 0.95,
            frameNumber: 10,
            timestamp: timestamp
        )
        
        XCTAssertEqual(detection.objectClass, .ball)
        XCTAssertEqual(detection.boundingBox, boundingBox)
        XCTAssertEqual(detection.confidence, 0.95)
        XCTAssertEqual(detection.frameNumber, 10)
        XCTAssertEqual(detection.timestamp.seconds, 1.5, accuracy: 0.01)
    }
    
    func testDetectionCodable() throws {
        let timestamp = CMTime(seconds: 2.0, preferredTimescale: 600)
        let boundingBox = CGRect(x: 0.5, y: 0.5, width: 0.1, height: 0.1)
        
        let detection = Detection(
            objectClass: .player,
            boundingBox: boundingBox,
            confidence: 0.88,
            frameNumber: 20,
            timestamp: timestamp
        )
        
        let encoded = try JSONEncoder().encode(detection)
        let decoded = try JSONDecoder().decode(Detection.self, from: encoded)
        
        XCTAssertEqual(decoded.id, detection.id)
        XCTAssertEqual(decoded.objectClass, detection.objectClass)
        XCTAssertEqual(decoded.boundingBox, detection.boundingBox)
        XCTAssertEqual(decoded.confidence, detection.confidence)
        XCTAssertEqual(decoded.frameNumber, detection.frameNumber)
        XCTAssertEqual(decoded.timestamp.seconds, detection.timestamp.seconds, accuracy: 0.01)
    }
    
    func testDetectionConfidenceRange() {
        let timestamp = CMTime(seconds: 1.0, preferredTimescale: 600)
        let boundingBox = CGRect(x: 0.0, y: 0.0, width: 0.5, height: 0.5)
        
        // Test minimum confidence
        let minDetection = Detection(
            objectClass: .ball,
            boundingBox: boundingBox,
            confidence: 0.0,
            frameNumber: 1,
            timestamp: timestamp
        )
        XCTAssertEqual(minDetection.confidence, 0.0)
        
        // Test maximum confidence
        let maxDetection = Detection(
            objectClass: .ball,
            boundingBox: boundingBox,
            confidence: 1.0,
            frameNumber: 1,
            timestamp: timestamp
        )
        XCTAssertEqual(maxDetection.confidence, 1.0)
    }
    
    // MARK: - Track Tests
    
    func testTrackInitialization() {
        let startTime = CMTime(seconds: 1.0, preferredTimescale: 600)
        let endTime = CMTime(seconds: 3.0, preferredTimescale: 600)
        
        let detection1 = Detection(
            objectClass: .ball,
            boundingBox: CGRect(x: 0.1, y: 0.1, width: 0.05, height: 0.05),
            confidence: 0.9,
            frameNumber: 10,
            timestamp: startTime
        )
        
        let detection2 = Detection(
            objectClass: .ball,
            boundingBox: CGRect(x: 0.2, y: 0.2, width: 0.05, height: 0.05),
            confidence: 0.85,
            frameNumber: 20,
            timestamp: endTime
        )
        
        let track = Track(
            objectClass: .ball,
            detections: [detection1, detection2],
            startTime: startTime,
            endTime: endTime,
            averageConfidence: 0.875
        )
        
        XCTAssertEqual(track.objectClass, .ball)
        XCTAssertEqual(track.detections.count, 2)
        XCTAssertEqual(track.startTime.seconds, 1.0, accuracy: 0.01)
        XCTAssertEqual(track.endTime.seconds, 3.0, accuracy: 0.01)
        XCTAssertEqual(track.averageConfidence, 0.875)
    }
    
    func testTrackDuration() {
        let startTime = CMTime(seconds: 1.0, preferredTimescale: 600)
        let endTime = CMTime(seconds: 5.5, preferredTimescale: 600)
        
        let track = Track(
            objectClass: .player,
            detections: [],
            startTime: startTime,
            endTime: endTime,
            averageConfidence: 0.9
        )
        
        XCTAssertEqual(track.duration, 4.5, accuracy: 0.01)
    }
    
    func testTrackTrajectory() {
        let startTime = CMTime(seconds: 1.0, preferredTimescale: 600)
        let endTime = CMTime(seconds: 2.0, preferredTimescale: 600)
        
        let detection1 = Detection(
            objectClass: .ball,
            boundingBox: CGRect(x: 0.1, y: 0.1, width: 0.05, height: 0.05),
            confidence: 0.9,
            frameNumber: 10,
            timestamp: startTime
        )
        
        let detection2 = Detection(
            objectClass: .ball,
            boundingBox: CGRect(x: 0.3, y: 0.4, width: 0.05, height: 0.05),
            confidence: 0.85,
            frameNumber: 20,
            timestamp: endTime
        )
        
        let track = Track(
            objectClass: .ball,
            detections: [detection1, detection2],
            startTime: startTime,
            endTime: endTime,
            averageConfidence: 0.875
        )
        
        let trajectory = track.trajectory
        XCTAssertEqual(trajectory.count, 2)
        XCTAssertEqual(trajectory[0].x, 0.125, accuracy: 0.001) // midX of first box
        XCTAssertEqual(trajectory[0].y, 0.125, accuracy: 0.001) // midY of first box
        XCTAssertEqual(trajectory[1].x, 0.325, accuracy: 0.001) // midX of second box
        XCTAssertEqual(trajectory[1].y, 0.425, accuracy: 0.001) // midY of second box
    }
    
    func testTrackCodable() throws {
        let startTime = CMTime(seconds: 1.0, preferredTimescale: 600)
        let endTime = CMTime(seconds: 2.0, preferredTimescale: 600)
        
        let detection = Detection(
            objectClass: .paddle,
            boundingBox: CGRect(x: 0.5, y: 0.5, width: 0.1, height: 0.1),
            confidence: 0.92,
            frameNumber: 15,
            timestamp: startTime
        )
        
        let track = Track(
            objectClass: .paddle,
            detections: [detection],
            startTime: startTime,
            endTime: endTime,
            averageConfidence: 0.92
        )
        
        let encoded = try JSONEncoder().encode(track)
        let decoded = try JSONDecoder().decode(Track.self, from: encoded)
        
        XCTAssertEqual(decoded.id, track.id)
        XCTAssertEqual(decoded.objectClass, track.objectClass)
        XCTAssertEqual(decoded.detections.count, track.detections.count)
        XCTAssertEqual(decoded.averageConfidence, track.averageConfidence)
        XCTAssertEqual(decoded.startTime.seconds, track.startTime.seconds, accuracy: 0.01)
        XCTAssertEqual(decoded.endTime.seconds, track.endTime.seconds, accuracy: 0.01)
        XCTAssertEqual(decoded.duration, track.duration, accuracy: 0.01)
    }
    
    func testTrackWithMultipleDetections() {
        let startTime = CMTime(seconds: 0.0, preferredTimescale: 600)
        let midTime = CMTime(seconds: 1.0, preferredTimescale: 600)
        let endTime = CMTime(seconds: 2.0, preferredTimescale: 600)
        
        let detections = [
            Detection(
                objectClass: .player,
                boundingBox: CGRect(x: 0.1, y: 0.1, width: 0.2, height: 0.3),
                confidence: 0.95,
                frameNumber: 0,
                timestamp: startTime
            ),
            Detection(
                objectClass: .player,
                boundingBox: CGRect(x: 0.2, y: 0.15, width: 0.2, height: 0.3),
                confidence: 0.93,
                frameNumber: 10,
                timestamp: midTime
            ),
            Detection(
                objectClass: .player,
                boundingBox: CGRect(x: 0.3, y: 0.2, width: 0.2, height: 0.3),
                confidence: 0.91,
                frameNumber: 20,
                timestamp: endTime
            )
        ]
        
        let track = Track(
            objectClass: .player,
            detections: detections,
            startTime: startTime,
            endTime: endTime,
            averageConfidence: 0.93
        )
        
        XCTAssertEqual(track.detections.count, 3)
        XCTAssertEqual(track.trajectory.count, 3)
        XCTAssertEqual(track.duration, 2.0, accuracy: 0.01)
    }
    
    // MARK: - VideoFrame Tests
    
    func testVideoFrameInitialization() {
        // Create a simple 1x1 CGImage for testing
        let colorSpace = CGColorSpaceCreateDeviceRGB()
        let bitmapInfo = CGBitmapInfo(rawValue: CGImageAlphaInfo.premultipliedLast.rawValue)
        
        guard let context = CGContext(
            data: nil,
            width: 1,
            height: 1,
            bitsPerComponent: 8,
            bytesPerRow: 4,
            space: colorSpace,
            bitmapInfo: bitmapInfo.rawValue
        ),
        let cgImage = context.makeImage() else {
            XCTFail("Failed to create test image")
            return
        }
        
        let timestamp = CMTime(seconds: 1.5, preferredTimescale: 600)
        let frame = VideoFrame(
            image: cgImage,
            timestamp: timestamp,
            frameNumber: 45
        )
        
        XCTAssertEqual(frame.frameNumber, 45)
        XCTAssertEqual(frame.timestamp.seconds, 1.5, accuracy: 0.01)
        XCTAssertNotNil(frame.image)
    }

    // MARK: - CourtPosition Tests
    
    func testCourtPositionInitialization() {
        let timestamp = CMTime(seconds: 1.0, preferredTimescale: 600)
        let position = CourtPosition(x: 0.5, y: 0.7, timestamp: timestamp)
        
        XCTAssertEqual(position.x, 0.5)
        XCTAssertEqual(position.y, 0.7)
        XCTAssertEqual(position.timestamp.seconds, 1.0, accuracy: 0.01)
    }
    
    func testCourtPositionCodable() throws {
        let timestamp = CMTime(seconds: 2.5, preferredTimescale: 600)
        let position = CourtPosition(x: 0.3, y: 0.8, timestamp: timestamp)
        
        let encoded = try JSONEncoder().encode(position)
        let decoded = try JSONDecoder().decode(CourtPosition.self, from: encoded)
        
        XCTAssertEqual(decoded.x, position.x)
        XCTAssertEqual(decoded.y, position.y)
        XCTAssertEqual(decoded.timestamp.seconds, position.timestamp.seconds, accuracy: 0.01)
    }
    
    // MARK: - CourtZone Tests
    
    func testCourtZoneRawValues() {
        XCTAssertEqual(CourtZone.frontLeft.rawValue, "frontLeft")
        XCTAssertEqual(CourtZone.frontCenter.rawValue, "frontCenter")
        XCTAssertEqual(CourtZone.frontRight.rawValue, "frontRight")
        XCTAssertEqual(CourtZone.midLeft.rawValue, "midLeft")
        XCTAssertEqual(CourtZone.midCenter.rawValue, "midCenter")
        XCTAssertEqual(CourtZone.midRight.rawValue, "midRight")
        XCTAssertEqual(CourtZone.backLeft.rawValue, "backLeft")
        XCTAssertEqual(CourtZone.backCenter.rawValue, "backCenter")
        XCTAssertEqual(CourtZone.backRight.rawValue, "backRight")
    }
    
    // MARK: - CourtCoverage Tests
    
    func testCourtCoverageInitialization() {
        let zones: [CourtZone: Double] = [
            .frontLeft: 0.1,
            .frontCenter: 0.2,
            .frontRight: 0.1,
            .midLeft: 0.15,
            .midCenter: 0.2,
            .midRight: 0.15,
            .backLeft: 0.03,
            .backCenter: 0.05,
            .backRight: 0.02
        ]
        
        let coverage = CourtCoverage(
            zones: zones,
            leftRightBalance: -0.2,
            kitchenLineProximity: 0.15,
            baselineProximity: 0.45
        )
        
        XCTAssertEqual(coverage.zones.count, 9)
        XCTAssertEqual(coverage.leftRightBalance, -0.2)
        XCTAssertEqual(coverage.kitchenLineProximity, 0.15)
        XCTAssertEqual(coverage.baselineProximity, 0.45)
    }
    
    func testCourtCoverageCodable() throws {
        let zones: [CourtZone: Double] = [
            .frontCenter: 0.5,
            .midCenter: 0.3,
            .backCenter: 0.2
        ]
        
        let coverage = CourtCoverage(
            zones: zones,
            leftRightBalance: 0.0,
            kitchenLineProximity: 0.1,
            baselineProximity: 0.5
        )
        
        let encoded = try JSONEncoder().encode(coverage)
        let decoded = try JSONDecoder().decode(CourtCoverage.self, from: encoded)
        
        XCTAssertEqual(decoded.zones.count, coverage.zones.count)
        XCTAssertEqual(decoded.leftRightBalance, coverage.leftRightBalance)
        XCTAssertEqual(decoded.kitchenLineProximity, coverage.kitchenLineProximity)
        XCTAssertEqual(decoded.baselineProximity, coverage.baselineProximity)
    }
    
    // MARK: - Shot Analysis Enum Tests
    
    func testShotDirectionRawValues() {
        XCTAssertEqual(ShotDirection.crossCourt.rawValue, "crossCourt")
        XCTAssertEqual(ShotDirection.downTheLine.rawValue, "downTheLine")
        XCTAssertEqual(ShotDirection.middle.rawValue, "middle")
    }
    
    func testShotDepthRawValues() {
        XCTAssertEqual(ShotDepth.kitchen.rawValue, "kitchen")
        XCTAssertEqual(ShotDepth.midCourt.rawValue, "midCourt")
        XCTAssertEqual(ShotDepth.baseline.rawValue, "baseline")
    }
    
    // MARK: - Contact Point Enum Tests
    
    func testContactSideRawValues() {
        XCTAssertEqual(ContactSide.forehand.rawValue, "forehand")
        XCTAssertEqual(ContactSide.backhand.rawValue, "backhand")
        XCTAssertEqual(ContactSide.middle.rawValue, "middle")
    }
    
    func testContactTimingRawValues() {
        XCTAssertEqual(ContactTiming.early.rawValue, "early")
        XCTAssertEqual(ContactTiming.onTime.rawValue, "onTime")
        XCTAssertEqual(ContactTiming.late.rawValue, "late")
    }
    
    // MARK: - Rally Outcome Tests
    
    func testRallyOutcomeRawValues() {
        XCTAssertEqual(RallyOutcome.winner.rawValue, "winner")
        XCTAssertEqual(RallyOutcome.error.rawValue, "error")
        XCTAssertEqual(RallyOutcome.unknown.rawValue, "unknown")
    }
    
    // MARK: - Issue Type Tests
    
    func testIssueTypeRawValues() {
        XCTAssertEqual(IssueType.staticPositioning.rawValue, "staticPositioning")
        XCTAssertEqual(IssueType.depthPositioning.rawValue, "depthPositioning")
        XCTAssertEqual(IssueType.reactionTiming.rawValue, "reactionTiming")
        XCTAssertEqual(IssueType.coverageImbalance.rawValue, "coverageImbalance")
        XCTAssertEqual(IssueType.sideSpecificTiming.rawValue, "sideSpecificTiming")
        XCTAssertEqual(IssueType.recoveryPositioning.rawValue, "recoveryPositioning")
    }
    
    // MARK: - BallTrajectory Tests
    
    func testBallTrajectoryInitialization() {
        let startTime = CMTime(seconds: 1.0, preferredTimescale: 600)
        let endTime = CMTime(seconds: 2.0, preferredTimescale: 600)
        
        let detection = Detection(
            objectClass: .ball,
            boundingBox: CGRect(x: 0.5, y: 0.5, width: 0.05, height: 0.05),
            confidence: 0.9,
            frameNumber: 10,
            timestamp: startTime
        )
        
        let track = Track(
            objectClass: .ball,
            detections: [detection],
            startTime: startTime,
            endTime: endTime,
            averageConfidence: 0.9
        )
        
        let trajectory = BallTrajectory(
            track: track,
            direction: .crossCourt,
            depth: .kitchen,
            estimatedSpeed: 25.5,
            confidence: 0.85
        )
        
        XCTAssertEqual(trajectory.track.id, track.id)
        XCTAssertEqual(trajectory.direction, .crossCourt)
        XCTAssertEqual(trajectory.depth, .kitchen)
        XCTAssertEqual(trajectory.estimatedSpeed, 25.5)
        XCTAssertEqual(trajectory.confidence, 0.85)
    }
    
    func testBallTrajectoryCodable() throws {
        let startTime = CMTime(seconds: 1.0, preferredTimescale: 600)
        let endTime = CMTime(seconds: 2.0, preferredTimescale: 600)
        
        let detection = Detection(
            objectClass: .ball,
            boundingBox: CGRect(x: 0.5, y: 0.5, width: 0.05, height: 0.05),
            confidence: 0.9,
            frameNumber: 10,
            timestamp: startTime
        )
        
        let track = Track(
            objectClass: .ball,
            detections: [detection],
            startTime: startTime,
            endTime: endTime,
            averageConfidence: 0.9
        )
        
        let trajectory = BallTrajectory(
            track: track,
            direction: .downTheLine,
            depth: .baseline,
            estimatedSpeed: 30.0,
            confidence: 0.88
        )
        
        let encoded = try JSONEncoder().encode(trajectory)
        let decoded = try JSONDecoder().decode(BallTrajectory.self, from: encoded)
        
        XCTAssertEqual(decoded.id, trajectory.id)
        XCTAssertEqual(decoded.direction, trajectory.direction)
        XCTAssertEqual(decoded.depth, trajectory.depth)
        XCTAssertEqual(decoded.estimatedSpeed, trajectory.estimatedSpeed)
        XCTAssertEqual(decoded.confidence, trajectory.confidence)
    }
    
    // MARK: - PlayerMovement Tests
    
    func testPlayerMovementInitialization() {
        let timestamp = CMTime(seconds: 1.0, preferredTimescale: 600)
        let zones: [CourtZone: Double] = [.frontCenter: 0.6, .midCenter: 0.4]
        
        let coverage = CourtCoverage(
            zones: zones,
            leftRightBalance: 0.1,
            kitchenLineProximity: 0.2,
            baselineProximity: 0.5
        )
        
        let positions = [
            CourtPosition(x: 0.5, y: 0.7, timestamp: timestamp)
        ]
        
        let movement = PlayerMovement(
            courtCoverage: coverage,
            movementSpeed: [2.5, 3.0, 2.8],
            positioningHistory: positions,
            recoveryPositions: positions,
            confidence: 0.9
        )
        
        XCTAssertEqual(movement.movementSpeed.count, 3)
        XCTAssertEqual(movement.positioningHistory.count, 1)
        XCTAssertEqual(movement.recoveryPositions.count, 1)
        XCTAssertEqual(movement.confidence, 0.9)
    }
    
    func testPlayerMovementCodable() throws {
        let timestamp = CMTime(seconds: 1.0, preferredTimescale: 600)
        let zones: [CourtZone: Double] = [.frontCenter: 1.0]
        
        let coverage = CourtCoverage(
            zones: zones,
            leftRightBalance: 0.0,
            kitchenLineProximity: 0.15,
            baselineProximity: 0.6
        )
        
        let positions = [
            CourtPosition(x: 0.5, y: 0.7, timestamp: timestamp)
        ]
        
        let movement = PlayerMovement(
            courtCoverage: coverage,
            movementSpeed: [2.0],
            positioningHistory: positions,
            recoveryPositions: positions,
            confidence: 0.85
        )
        
        let encoded = try JSONEncoder().encode(movement)
        let decoded = try JSONDecoder().decode(PlayerMovement.self, from: encoded)
        
        XCTAssertEqual(decoded.movementSpeed.count, movement.movementSpeed.count)
        XCTAssertEqual(decoded.positioningHistory.count, movement.positioningHistory.count)
        XCTAssertEqual(decoded.confidence, movement.confidence)
    }
    
    // MARK: - ContactPoint Tests
    
    func testContactPointInitialization() {
        let timestamp = CMTime(seconds: 1.5, preferredTimescale: 600)
        let location = CGPoint(x: 0.2, y: 0.3)
        
        let contact = ContactPoint(
            timestamp: timestamp,
            location: location,
            side: .forehand,
            timing: .onTime,
            confidence: 0.92
        )
        
        XCTAssertEqual(contact.timestamp.seconds, 1.5, accuracy: 0.01)
        XCTAssertEqual(contact.location, location)
        XCTAssertEqual(contact.side, .forehand)
        XCTAssertEqual(contact.timing, .onTime)
        XCTAssertEqual(contact.confidence, 0.92)
    }
    
    func testContactPointCodable() throws {
        let timestamp = CMTime(seconds: 2.0, preferredTimescale: 600)
        let location = CGPoint(x: -0.1, y: 0.4)
        
        let contact = ContactPoint(
            timestamp: timestamp,
            location: location,
            side: .backhand,
            timing: .late,
            confidence: 0.78
        )
        
        let encoded = try JSONEncoder().encode(contact)
        let decoded = try JSONDecoder().decode(ContactPoint.self, from: encoded)
        
        XCTAssertEqual(decoded.id, contact.id)
        XCTAssertEqual(decoded.timestamp.seconds, contact.timestamp.seconds, accuracy: 0.01)
        XCTAssertEqual(decoded.location, contact.location)
        XCTAssertEqual(decoded.side, contact.side)
        XCTAssertEqual(decoded.timing, contact.timing)
        XCTAssertEqual(decoded.confidence, contact.confidence)
    }
    
    // MARK: - Rally Tests
    
    func testRallyInitialization() {
        let startTime = CMTime(seconds: 10.0, preferredTimescale: 600)
        let endTime = CMTime(seconds: 25.5, preferredTimescale: 600)
        
        let rally = Rally(
            startTime: startTime,
            endTime: endTime,
            shotCount: 12,
            outcome: .winner
        )
        
        XCTAssertEqual(rally.startTime.seconds, 10.0, accuracy: 0.01)
        XCTAssertEqual(rally.endTime.seconds, 25.5, accuracy: 0.01)
        XCTAssertEqual(rally.shotCount, 12)
        XCTAssertEqual(rally.outcome, .winner)
    }
    
    func testRallyDuration() {
        let startTime = CMTime(seconds: 5.0, preferredTimescale: 600)
        let endTime = CMTime(seconds: 12.5, preferredTimescale: 600)
        
        let rally = Rally(
            startTime: startTime,
            endTime: endTime,
            shotCount: 8,
            outcome: .error
        )
        
        XCTAssertEqual(rally.duration, 7.5, accuracy: 0.01)
    }
    
    func testRallyCodable() throws {
        let startTime = CMTime(seconds: 1.0, preferredTimescale: 600)
        let endTime = CMTime(seconds: 8.0, preferredTimescale: 600)
        
        let rally = Rally(
            startTime: startTime,
            endTime: endTime,
            shotCount: 6,
            outcome: .unknown
        )
        
        let encoded = try JSONEncoder().encode(rally)
        let decoded = try JSONDecoder().decode(Rally.self, from: encoded)
        
        XCTAssertEqual(decoded.id, rally.id)
        XCTAssertEqual(decoded.startTime.seconds, rally.startTime.seconds, accuracy: 0.01)
        XCTAssertEqual(decoded.endTime.seconds, rally.endTime.seconds, accuracy: 0.01)
        XCTAssertEqual(decoded.shotCount, rally.shotCount)
        XCTAssertEqual(decoded.outcome, rally.outcome)
        XCTAssertEqual(decoded.duration, rally.duration, accuracy: 0.01)
    }
    
    // MARK: - PerformanceIssue Tests
    
    func testPerformanceIssueInitialization() {
        let issue = PerformanceIssue(
            type: .staticPositioning,
            severity: 0.75,
            occurrences: 8,
            description: "Player stays in same zone for extended periods",
            confidence: 0.88
        )
        
        XCTAssertEqual(issue.type, .staticPositioning)
        XCTAssertEqual(issue.severity, 0.75)
        XCTAssertEqual(issue.occurrences, 8)
        XCTAssertEqual(issue.description, "Player stays in same zone for extended periods")
        XCTAssertEqual(issue.confidence, 0.88)
    }
    
    func testPerformanceIssueCodable() throws {
        let issue = PerformanceIssue(
            type: .coverageImbalance,
            severity: 0.6,
            occurrences: 5,
            description: "Court coverage stronger on left side",
            confidence: 0.82
        )
        
        let encoded = try JSONEncoder().encode(issue)
        let decoded = try JSONDecoder().decode(PerformanceIssue.self, from: encoded)
        
        XCTAssertEqual(decoded.id, issue.id)
        XCTAssertEqual(decoded.type, issue.type)
        XCTAssertEqual(decoded.severity, issue.severity)
        XCTAssertEqual(decoded.occurrences, issue.occurrences)
        XCTAssertEqual(decoded.description, issue.description)
        XCTAssertEqual(decoded.confidence, issue.confidence)
    }
    
    // MARK: - PerformanceFeatures Tests
    
    func testPerformanceFeaturesInitialization() {
        let timestamp = CMTime(seconds: 1.0, preferredTimescale: 600)
        let zones: [CourtZone: Double] = [.frontCenter: 1.0]
        
        let coverage = CourtCoverage(
            zones: zones,
            leftRightBalance: 0.0,
            kitchenLineProximity: 0.2,
            baselineProximity: 0.5
        )
        
        let movement = PlayerMovement(
            courtCoverage: coverage,
            movementSpeed: [2.5],
            positioningHistory: [],
            recoveryPositions: [],
            confidence: 0.9
        )
        
        let features = PerformanceFeatures(
            ballTrajectories: [],
            playerMovement: movement,
            contactPoints: [],
            rallies: [],
            issues: [],
            confidence: 0.85
        )
        
        XCTAssertEqual(features.ballTrajectories.count, 0)
        XCTAssertEqual(features.contactPoints.count, 0)
        XCTAssertEqual(features.rallies.count, 0)
        XCTAssertEqual(features.issues.count, 0)
        XCTAssertEqual(features.confidence, 0.85)
    }
    
    func testPerformanceFeaturesCodable() throws {
        let timestamp = CMTime(seconds: 1.0, preferredTimescale: 600)
        let zones: [CourtZone: Double] = [.midCenter: 1.0]
        
        let coverage = CourtCoverage(
            zones: zones,
            leftRightBalance: 0.1,
            kitchenLineProximity: 0.15,
            baselineProximity: 0.6
        )
        
        let movement = PlayerMovement(
            courtCoverage: coverage,
            movementSpeed: [3.0],
            positioningHistory: [],
            recoveryPositions: [],
            confidence: 0.88
        )
        
        let issue = PerformanceIssue(
            type: .depthPositioning,
            severity: 0.7,
            occurrences: 6,
            description: "Too far from kitchen line",
            confidence: 0.85
        )
        
        let features = PerformanceFeatures(
            ballTrajectories: [],
            playerMovement: movement,
            contactPoints: [],
            rallies: [],
            issues: [issue],
            confidence: 0.87
        )
        
        let encoded = try JSONEncoder().encode(features)
        let decoded = try JSONDecoder().decode(PerformanceFeatures.self, from: encoded)
        
        XCTAssertEqual(decoded.ballTrajectories.count, features.ballTrajectories.count)
        XCTAssertEqual(decoded.contactPoints.count, features.contactPoints.count)
        XCTAssertEqual(decoded.rallies.count, features.rallies.count)
        XCTAssertEqual(decoded.issues.count, features.issues.count)
        XCTAssertEqual(decoded.confidence, features.confidence)
    }
    
    func testPerformanceFeaturesWithCompleteData() throws {
        let startTime = CMTime(seconds: 1.0, preferredTimescale: 600)
        let endTime = CMTime(seconds: 2.0, preferredTimescale: 600)
        
        // Create ball trajectory
        let detection = Detection(
            objectClass: .ball,
            boundingBox: CGRect(x: 0.5, y: 0.5, width: 0.05, height: 0.05),
            confidence: 0.9,
            frameNumber: 10,
            timestamp: startTime
        )
        
        let track = Track(
            objectClass: .ball,
            detections: [detection],
            startTime: startTime,
            endTime: endTime,
            averageConfidence: 0.9
        )
        
        let trajectory = BallTrajectory(
            track: track,
            direction: .crossCourt,
            depth: .kitchen,
            estimatedSpeed: 25.0,
            confidence: 0.88
        )
        
        // Create player movement
        let zones: [CourtZone: Double] = [
            .frontCenter: 0.5,
            .midCenter: 0.3,
            .backCenter: 0.2
        ]
        
        let coverage = CourtCoverage(
            zones: zones,
            leftRightBalance: 0.0,
            kitchenLineProximity: 0.2,
            baselineProximity: 0.5
        )
        
        let movement = PlayerMovement(
            courtCoverage: coverage,
            movementSpeed: [2.5, 3.0],
            positioningHistory: [CourtPosition(x: 0.5, y: 0.7, timestamp: startTime)],
            recoveryPositions: [CourtPosition(x: 0.5, y: 0.6, timestamp: endTime)],
            confidence: 0.9
        )
        
        // Create contact point
        let contact = ContactPoint(
            timestamp: startTime,
            location: CGPoint(x: 0.1, y: 0.2),
            side: .forehand,
            timing: .onTime,
            confidence: 0.85
        )
        
        // Create rally
        let rally = Rally(
            startTime: startTime,
            endTime: endTime,
            shotCount: 8,
            outcome: .winner
        )
        
        // Create issue
        let issue = PerformanceIssue(
            type: .staticPositioning,
            severity: 0.6,
            occurrences: 5,
            description: "Stays in same zone too long",
            confidence: 0.8
        )
        
        // Create complete features
        let features = PerformanceFeatures(
            ballTrajectories: [trajectory],
            playerMovement: movement,
            contactPoints: [contact],
            rallies: [rally],
            issues: [issue],
            confidence: 0.87
        )
        
        // Test encoding/decoding
        let encoded = try JSONEncoder().encode(features)
        let decoded = try JSONDecoder().decode(PerformanceFeatures.self, from: encoded)
        
        XCTAssertEqual(decoded.ballTrajectories.count, 1)
        XCTAssertEqual(decoded.contactPoints.count, 1)
        XCTAssertEqual(decoded.rallies.count, 1)
        XCTAssertEqual(decoded.issues.count, 1)
        XCTAssertEqual(decoded.confidence, 0.87)
        
        // Verify nested data
        XCTAssertEqual(decoded.ballTrajectories[0].direction, .crossCourt)
        XCTAssertEqual(decoded.contactPoints[0].side, .forehand)
        XCTAssertEqual(decoded.rallies[0].outcome, .winner)
        XCTAssertEqual(decoded.issues[0].type, .staticPositioning)
    }

    // MARK: - CoachingInsight Tests
    
    func testCoachingInsightInitialization() {
        let insight = CoachingInsight(
            title: "Static Positioning",
            description: "You tend to stay in the same zone for extended periods",
            severity: 0.75,
            confidence: 0.88
        )
        
        XCTAssertEqual(insight.title, "Static Positioning")
        XCTAssertEqual(insight.description, "You tend to stay in the same zone for extended periods")
        XCTAssertEqual(insight.severity, 0.75)
        XCTAssertEqual(insight.confidence, 0.88)
    }
    
    func testCoachingInsightCodable() throws {
        let insight = CoachingInsight(
            title: "Late Contact",
            description: "You are often contacting the ball late on your right side",
            severity: 0.65,
            confidence: 0.82
        )
        
        let encoded = try JSONEncoder().encode(insight)
        let decoded = try JSONDecoder().decode(CoachingInsight.self, from: encoded)
        
        XCTAssertEqual(decoded.id, insight.id)
        XCTAssertEqual(decoded.title, insight.title)
        XCTAssertEqual(decoded.description, insight.description)
        XCTAssertEqual(decoded.severity, insight.severity)
        XCTAssertEqual(decoded.confidence, insight.confidence)
    }
    
    func testCoachingInsightSeverityRange() {
        let lowSeverity = CoachingInsight(
            title: "Minor Issue",
            description: "Small improvement area",
            severity: 0.1,
            confidence: 0.9
        )
        XCTAssertEqual(lowSeverity.severity, 0.1)
        
        let highSeverity = CoachingInsight(
            title: "Critical Issue",
            description: "Major improvement needed",
            severity: 1.0,
            confidence: 0.95
        )
        XCTAssertEqual(highSeverity.severity, 1.0)
    }
    
    // MARK: - PracticeSuggestion Tests
    
    func testPracticeSuggestionInitialization() {
        let suggestion = PracticeSuggestion(
            issue: .staticPositioning,
            drill: "Shadowing drill",
            description: "Practice moving to different court positions without a ball"
        )
        
        XCTAssertEqual(suggestion.issue, .staticPositioning)
        XCTAssertEqual(suggestion.drill, "Shadowing drill")
        XCTAssertEqual(suggestion.description, "Practice moving to different court positions without a ball")
    }
    
    func testPracticeSuggestionCodable() throws {
        let suggestion = PracticeSuggestion(
            issue: .depthPositioning,
            drill: "Kitchen line drill",
            description: "Practice dinking while maintaining position at the kitchen line"
        )
        
        let encoded = try JSONEncoder().encode(suggestion)
        let decoded = try JSONDecoder().decode(PracticeSuggestion.self, from: encoded)
        
        XCTAssertEqual(decoded.id, suggestion.id)
        XCTAssertEqual(decoded.issue, suggestion.issue)
        XCTAssertEqual(decoded.drill, suggestion.drill)
        XCTAssertEqual(decoded.description, suggestion.description)
    }
    
    func testPracticeSuggestionForAllIssueTypes() {
        let issueTypes: [IssueType] = [
            .staticPositioning,
            .depthPositioning,
            .reactionTiming,
            .coverageImbalance,
            .sideSpecificTiming,
            .recoveryPositioning
        ]
        
        for issueType in issueTypes {
            let suggestion = PracticeSuggestion(
                issue: issueType,
                drill: "Test drill for \(issueType.rawValue)",
                description: "Test description"
            )
            XCTAssertEqual(suggestion.issue, issueType)
        }
    }
    
    // MARK: - CoachingFeedback Tests
    
    func testCoachingFeedbackInitialization() {
        let insight = CoachingInsight(
            title: "Positioning Issue",
            description: "You tend to stay too far behind the kitchen line",
            severity: 0.7,
            confidence: 0.85
        )
        
        let suggestion = PracticeSuggestion(
            issue: .depthPositioning,
            drill: "Kitchen line drill",
            description: "Practice maintaining position at the kitchen line"
        )
        
        let feedback = CoachingFeedback(
            insights: [insight],
            practiceSuggestions: [suggestion],
            quickTips: ["Stay on your toes", "Move forward after your return"],
            nextSessionFocus: ["Work on court positioning", "Practice recovery to center"]
        )
        
        XCTAssertEqual(feedback.insights.count, 1)
        XCTAssertEqual(feedback.practiceSuggestions.count, 1)
        XCTAssertEqual(feedback.quickTips.count, 2)
        XCTAssertEqual(feedback.nextSessionFocus.count, 2)
    }
    
    func testCoachingFeedbackCodable() throws {
        let insight1 = CoachingInsight(
            title: "Static Positioning",
            description: "You stay in the same zone too long",
            severity: 0.75,
            confidence: 0.88
        )
        
        let insight2 = CoachingInsight(
            title: "Coverage Imbalance",
            description: "Your court coverage is stronger on the left side",
            severity: 0.65,
            confidence: 0.82
        )
        
        let suggestion1 = PracticeSuggestion(
            issue: .staticPositioning,
            drill: "Shadowing drill",
            description: "Practice moving to different positions"
        )
        
        let suggestion2 = PracticeSuggestion(
            issue: .coverageImbalance,
            drill: "Side-to-side drill",
            description: "Practice moving to your weak side"
        )
        
        let feedback = CoachingFeedback(
            insights: [insight1, insight2],
            practiceSuggestions: [suggestion1, suggestion2],
            quickTips: ["Stay mobile", "Keep your paddle up"],
            nextSessionFocus: ["Court positioning", "Movement patterns"]
        )
        
        let encoded = try JSONEncoder().encode(feedback)
        let decoded = try JSONDecoder().decode(CoachingFeedback.self, from: encoded)
        
        XCTAssertEqual(decoded.insights.count, feedback.insights.count)
        XCTAssertEqual(decoded.practiceSuggestions.count, feedback.practiceSuggestions.count)
        XCTAssertEqual(decoded.quickTips.count, feedback.quickTips.count)
        XCTAssertEqual(decoded.nextSessionFocus.count, feedback.nextSessionFocus.count)
        
        // Verify first insight
        XCTAssertEqual(decoded.insights[0].title, insight1.title)
        XCTAssertEqual(decoded.insights[0].severity, insight1.severity)
        
        // Verify first suggestion
        XCTAssertEqual(decoded.practiceSuggestions[0].drill, suggestion1.drill)
        XCTAssertEqual(decoded.practiceSuggestions[0].issue, suggestion1.issue)
    }
    
    func testCoachingFeedbackEmpty() throws {
        let feedback = CoachingFeedback(
            insights: [],
            practiceSuggestions: [],
            quickTips: [],
            nextSessionFocus: []
        )
        
        XCTAssertEqual(feedback.insights.count, 0)
        XCTAssertEqual(feedback.practiceSuggestions.count, 0)
        XCTAssertEqual(feedback.quickTips.count, 0)
        XCTAssertEqual(feedback.nextSessionFocus.count, 0)
        
        // Verify it can be encoded/decoded
        let encoded = try JSONEncoder().encode(feedback)
        let decoded = try JSONDecoder().decode(CoachingFeedback.self, from: encoded)
        
        XCTAssertEqual(decoded.insights.count, 0)
        XCTAssertEqual(decoded.practiceSuggestions.count, 0)
    }
    
    func testCoachingFeedbackWithMaxInsights() throws {
        // Test with 5 insights (max per requirement 8.9)
        let insights = (1...5).map { i in
            CoachingInsight(
                title: "Issue \(i)",
                description: "Description \(i)",
                severity: Float(i) / 10.0,
                confidence: 0.8
            )
        }
        
        let feedback = CoachingFeedback(
            insights: insights,
            practiceSuggestions: [],
            quickTips: [],
            nextSessionFocus: []
        )
        
        XCTAssertEqual(feedback.insights.count, 5)
        
        // Verify encoding/decoding preserves all insights
        let encoded = try JSONEncoder().encode(feedback)
        let decoded = try JSONDecoder().decode(CoachingFeedback.self, from: encoded)
        
        XCTAssertEqual(decoded.insights.count, 5)
        for i in 0..<5 {
            XCTAssertEqual(decoded.insights[i].title, "Issue \(i+1)")
        }
    }
    
    func testCoachingFeedbackWithQualifyingLanguage() {
        // Test marginal confidence (0.6-0.7) per requirement 8.8
        let marginalInsight = CoachingInsight(
            title: "Possible Timing Issue",
            description: "You appear to be contacting the ball late on your right side",
            severity: 0.5,
            confidence: 0.65
        )
        
        let feedback = CoachingFeedback(
            insights: [marginalInsight],
            practiceSuggestions: [],
            quickTips: [],
            nextSessionFocus: []
        )
        
        XCTAssertEqual(feedback.insights[0].confidence, 0.65)
        XCTAssertTrue(feedback.insights[0].description.contains("appear"))
    }
}
