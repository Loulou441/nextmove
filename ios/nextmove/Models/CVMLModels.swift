//
//  CVMLModels.swift
//  nextmove
//
//  Core data models for CV/ML video analysis system
//

import Foundation
import CoreGraphics
import AVFoundation

// MARK: - Object Class

/// Object classes that can be detected in video frames
enum ObjectClass: String, Codable {
    case ball
    case player
    case paddle
    case courtLine
    case net
    case netPost
}

// MARK: - Video Frame

/// Represents a single frame extracted from video with metadata
struct VideoFrame {
    let image: CGImage
    let timestamp: CMTime
    let frameNumber: Int
}

// MARK: - Detection

/// Single-frame object identification with bounding box and confidence
struct Detection: Codable, Identifiable {
    let id: UUID
    let objectClass: ObjectClass
    let boundingBox: CGRect // normalized coordinates (0-1)
    let confidence: Float // 0.0-1.0
    let frameNumber: Int
    let timestamp: CMTime
    
    init(
        id: UUID = UUID(),
        objectClass: ObjectClass,
        boundingBox: CGRect,
        confidence: Float,
        frameNumber: Int,
        timestamp: CMTime
    ) {
        self.id = id
        self.objectClass = objectClass
        self.boundingBox = boundingBox
        self.confidence = confidence
        self.frameNumber = frameNumber
        self.timestamp = timestamp
    }
    
    // Custom coding for CMTime
    enum CodingKeys: String, CodingKey {
        case id, objectClass, boundingBox, confidence, frameNumber
        case timestampValue, timestampTimescale
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(UUID.self, forKey: .id)
        objectClass = try container.decode(ObjectClass.self, forKey: .objectClass)
        boundingBox = try container.decode(CGRect.self, forKey: .boundingBox)
        confidence = try container.decode(Float.self, forKey: .confidence)
        frameNumber = try container.decode(Int.self, forKey: .frameNumber)
        
        let value = try container.decode(Int64.self, forKey: .timestampValue)
        let timescale = try container.decode(Int32.self, forKey: .timestampTimescale)
        timestamp = CMTime(value: CMTimeValue(value), timescale: timescale)
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encode(objectClass, forKey: .objectClass)
        try container.encode(boundingBox, forKey: .boundingBox)
        try container.encode(confidence, forKey: .confidence)
        try container.encode(frameNumber, forKey: .frameNumber)
        try container.encode(timestamp.value, forKey: .timestampValue)
        try container.encode(timestamp.timescale, forKey: .timestampTimescale)
    }
}

// MARK: - Track

/// Sequence of detections for the same object across multiple frames
struct Track: Codable, Identifiable {
    let id: UUID
    let objectClass: ObjectClass
    let detections: [Detection]
    let startTime: CMTime
    let endTime: CMTime
    let averageConfidence: Float
    
    init(
        id: UUID = UUID(),
        objectClass: ObjectClass,
        detections: [Detection],
        startTime: CMTime,
        endTime: CMTime,
        averageConfidence: Float
    ) {
        self.id = id
        self.objectClass = objectClass
        self.detections = detections
        self.startTime = startTime
        self.endTime = endTime
        self.averageConfidence = averageConfidence
    }
    
    /// Duration of the track in seconds
    var duration: TimeInterval {
        return endTime.seconds - startTime.seconds
    }
    
    /// Trajectory of the object as a sequence of center points
    var trajectory: [CGPoint] {
        return detections.map { detection in
            CGPoint(
                x: detection.boundingBox.midX,
                y: detection.boundingBox.midY
            )
        }
    }
    
    // Custom coding for CMTime
    enum CodingKeys: String, CodingKey {
        case id, objectClass, detections, averageConfidence
        case startTimeValue, startTimeTimescale
        case endTimeValue, endTimeTimescale
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(UUID.self, forKey: .id)
        objectClass = try container.decode(ObjectClass.self, forKey: .objectClass)
        detections = try container.decode([Detection].self, forKey: .detections)
        averageConfidence = try container.decode(Float.self, forKey: .averageConfidence)
        
        let startValue = try container.decode(Int64.self, forKey: .startTimeValue)
        let startTimescale = try container.decode(Int32.self, forKey: .startTimeTimescale)
        startTime = CMTime(value: CMTimeValue(startValue), timescale: startTimescale)
        
        let endValue = try container.decode(Int64.self, forKey: .endTimeValue)
        let endTimescale = try container.decode(Int32.self, forKey: .endTimeTimescale)
        endTime = CMTime(value: CMTimeValue(endValue), timescale: endTimescale)
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encode(objectClass, forKey: .objectClass)
        try container.encode(detections, forKey: .detections)
        try container.encode(averageConfidence, forKey: .averageConfidence)
        try container.encode(startTime.value, forKey: .startTimeValue)
        try container.encode(startTime.timescale, forKey: .startTimeTimescale)
        try container.encode(endTime.value, forKey: .endTimeValue)
        try container.encode(endTime.timescale, forKey: .endTimeTimescale)
    }
}

// MARK: - Court Position and Coverage

/// Normalized court coordinates (0.0 to 1.0)
struct CourtPosition: Codable {
    let x: Double // 0.0 (left) to 1.0 (right)
    let y: Double // 0.0 (baseline) to 1.0 (net)
    let timestamp: CMTime
    
    init(x: Double, y: Double, timestamp: CMTime) {
        self.x = x
        self.y = y
        self.timestamp = timestamp
    }
    
    // Custom coding for CMTime
    enum CodingKeys: String, CodingKey {
        case x, y
        case timestampValue, timestampTimescale
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        x = try container.decode(Double.self, forKey: .x)
        y = try container.decode(Double.self, forKey: .y)
        
        let value = try container.decode(Int64.self, forKey: .timestampValue)
        let timescale = try container.decode(Int32.self, forKey: .timestampTimescale)
        timestamp = CMTime(value: CMTimeValue(value), timescale: timescale)
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(x, forKey: .x)
        try container.encode(y, forKey: .y)
        try container.encode(timestamp.value, forKey: .timestampValue)
        try container.encode(timestamp.timescale, forKey: .timestampTimescale)
    }
}

/// Court zones for coverage analysis
enum CourtZone: String, Codable {
    case frontLeft
    case frontCenter
    case frontRight
    case midLeft
    case midCenter
    case midRight
    case backLeft
    case backCenter
    case backRight
}

/// Court coverage metrics
struct CourtCoverage: Codable {
    let zones: [CourtZone: Double] // zone -> time percentage
    let leftRightBalance: Double // -1.0 (all left) to 1.0 (all right)
    let kitchenLineProximity: Double // average distance
    let baselineProximity: Double
    
    init(
        zones: [CourtZone: Double],
        leftRightBalance: Double,
        kitchenLineProximity: Double,
        baselineProximity: Double
    ) {
        self.zones = zones
        self.leftRightBalance = leftRightBalance
        self.kitchenLineProximity = kitchenLineProximity
        self.baselineProximity = baselineProximity
    }
}

// MARK: - Shot Analysis Enums

/// Direction of a shot
enum ShotDirection: String, Codable {
    case crossCourt
    case downTheLine
    case middle
}

/// Depth of a shot on the court
enum ShotDepth: String, Codable {
    case kitchen
    case midCourt
    case baseline
}

// MARK: - Contact Point Enums

/// Side of contact relative to player
enum ContactSide: String, Codable {
    case forehand
    case backhand
    case middle
}

/// Timing of contact
enum ContactTiming: String, Codable {
    case early
    case onTime
    case late
}

// MARK: - Rally Outcome

/// Outcome of a rally
enum RallyOutcome: String, Codable {
    case winner
    case error
    case unknown
}

// MARK: - Performance Issue Type

/// Types of performance issues that can be detected
enum IssueType: String, Codable {
    case staticPositioning
    case depthPositioning
    case reactionTiming
    case coverageImbalance
    case sideSpecificTiming
    case recoveryPositioning
}

// MARK: - Ball Trajectory

/// Ball trajectory analysis with shot characteristics
struct BallTrajectory: Codable, Identifiable {
    let id: UUID
    let track: Track
    let direction: ShotDirection
    let depth: ShotDepth
    let estimatedSpeed: Double?
    let confidence: Float
    
    init(
        id: UUID = UUID(),
        track: Track,
        direction: ShotDirection,
        depth: ShotDepth,
        estimatedSpeed: Double?,
        confidence: Float
    ) {
        self.id = id
        self.track = track
        self.direction = direction
        self.depth = depth
        self.estimatedSpeed = estimatedSpeed
        self.confidence = confidence
    }
}

// MARK: - Player Movement

/// Player movement patterns and court coverage
struct PlayerMovement: Codable {
    let courtCoverage: CourtCoverage
    let movementSpeed: [Double]
    let positioningHistory: [CourtPosition]
    let recoveryPositions: [CourtPosition]
    let confidence: Float
    
    init(
        courtCoverage: CourtCoverage,
        movementSpeed: [Double],
        positioningHistory: [CourtPosition],
        recoveryPositions: [CourtPosition],
        confidence: Float
    ) {
        self.courtCoverage = courtCoverage
        self.movementSpeed = movementSpeed
        self.positioningHistory = positioningHistory
        self.recoveryPositions = recoveryPositions
        self.confidence = confidence
    }

    /// An empty player movement value, useful for constructing partial
    /// `PerformanceFeatures` instances (e.g. in tests or fallback paths).
    static var empty: PlayerMovement {
        PlayerMovement(
            courtCoverage: CourtCoverage(
                zones: [:],
                leftRightBalance: 0.0,
                kitchenLineProximity: 0.0,
                baselineProximity: 0.0
            ),
            movementSpeed: [],
            positioningHistory: [],
            recoveryPositions: [],
            confidence: 0.0
        )
    }
}

// MARK: - Contact Point

/// Contact point between paddle and ball
struct ContactPoint: Codable, Identifiable {
    let id: UUID
    let timestamp: CMTime
    let location: CGPoint // relative to player body
    let side: ContactSide
    let timing: ContactTiming
    let confidence: Float
    
    init(
        id: UUID = UUID(),
        timestamp: CMTime,
        location: CGPoint,
        side: ContactSide,
        timing: ContactTiming,
        confidence: Float
    ) {
        self.id = id
        self.timestamp = timestamp
        self.location = location
        self.side = side
        self.timing = timing
        self.confidence = confidence
    }
    
    // Custom coding for CMTime
    enum CodingKeys: String, CodingKey {
        case id, location, side, timing, confidence
        case timestampValue, timestampTimescale
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(UUID.self, forKey: .id)
        location = try container.decode(CGPoint.self, forKey: .location)
        side = try container.decode(ContactSide.self, forKey: .side)
        timing = try container.decode(ContactTiming.self, forKey: .timing)
        confidence = try container.decode(Float.self, forKey: .confidence)
        
        let value = try container.decode(Int64.self, forKey: .timestampValue)
        let timescale = try container.decode(Int32.self, forKey: .timestampTimescale)
        timestamp = CMTime(value: CMTimeValue(value), timescale: timescale)
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encode(location, forKey: .location)
        try container.encode(side, forKey: .side)
        try container.encode(timing, forKey: .timing)
        try container.encode(confidence, forKey: .confidence)
        try container.encode(timestamp.value, forKey: .timestampValue)
        try container.encode(timestamp.timescale, forKey: .timestampTimescale)
    }
}

// MARK: - Rally

/// Rally information with shot count and outcome
struct Rally: Codable, Identifiable {
    let id: UUID
    let startTime: CMTime
    let endTime: CMTime
    let shotCount: Int
    let outcome: RallyOutcome
    
    init(
        id: UUID = UUID(),
        startTime: CMTime,
        endTime: CMTime,
        shotCount: Int,
        outcome: RallyOutcome
    ) {
        self.id = id
        self.startTime = startTime
        self.endTime = endTime
        self.shotCount = shotCount
        self.outcome = outcome
    }
    
    /// Duration of the rally in seconds
    var duration: TimeInterval {
        return endTime.seconds - startTime.seconds
    }
    
    // Custom coding for CMTime
    enum CodingKeys: String, CodingKey {
        case id, shotCount, outcome
        case startTimeValue, startTimeTimescale
        case endTimeValue, endTimeTimescale
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(UUID.self, forKey: .id)
        shotCount = try container.decode(Int.self, forKey: .shotCount)
        outcome = try container.decode(RallyOutcome.self, forKey: .outcome)
        
        let startValue = try container.decode(Int64.self, forKey: .startTimeValue)
        let startTimescale = try container.decode(Int32.self, forKey: .startTimeTimescale)
        startTime = CMTime(value: CMTimeValue(startValue), timescale: startTimescale)
        
        let endValue = try container.decode(Int64.self, forKey: .endTimeValue)
        let endTimescale = try container.decode(Int32.self, forKey: .endTimeTimescale)
        endTime = CMTime(value: CMTimeValue(endValue), timescale: endTimescale)
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encode(shotCount, forKey: .shotCount)
        try container.encode(outcome, forKey: .outcome)
        try container.encode(startTime.value, forKey: .startTimeValue)
        try container.encode(startTime.timescale, forKey: .startTimeTimescale)
        try container.encode(endTime.value, forKey: .endTimeValue)
        try container.encode(endTime.timescale, forKey: .endTimeTimescale)
    }
}

// MARK: - Performance Issue

/// Detected performance issue with severity and description
struct PerformanceIssue: Codable, Identifiable {
    let id: UUID
    let type: IssueType
    let severity: Float // 0.0-1.0
    let occurrences: Int
    let description: String
    let confidence: Float
    
    init(
        id: UUID = UUID(),
        type: IssueType,
        severity: Float,
        occurrences: Int,
        description: String,
        confidence: Float
    ) {
        self.id = id
        self.type = type
        self.severity = severity
        self.occurrences = occurrences
        self.description = description
        self.confidence = confidence
    }
}

// MARK: - Performance Features

/// Aggregated performance features extracted from tracks
struct PerformanceFeatures: Codable {
    let ballTrajectories: [BallTrajectory]
    let playerMovement: PlayerMovement
    let contactPoints: [ContactPoint]
    let rallies: [Rally]
    let issues: [PerformanceIssue]
    let confidence: Float
    
    init(
        ballTrajectories: [BallTrajectory] = [],
        playerMovement: PlayerMovement = .empty,
        contactPoints: [ContactPoint] = [],
        rallies: [Rally] = [],
        issues: [PerformanceIssue] = [],
        confidence: Float = 0.0
    ) {
        self.ballTrajectories = ballTrajectories
        self.playerMovement = playerMovement
        self.contactPoints = contactPoints
        self.rallies = rallies
        self.issues = issues
        self.confidence = confidence
    }
}

// MARK: - Coaching Feedback Models

/// Individual coaching insight with severity and confidence
/// Validates: Requirements 8.1-8.10
struct CoachingInsight: Codable, Identifiable {
    let id: UUID
    let title: String
    let description: String
    let severity: Float // 0.0-1.0, higher means more significant
    let confidence: Float // 0.0-1.0
    
    init(
        id: UUID = UUID(),
        title: String,
        description: String,
        severity: Float,
        confidence: Float
    ) {
        self.id = id
        self.title = title
        self.description = description
        self.severity = severity
        self.confidence = confidence
    }
}

/// Practice suggestion for addressing a specific issue
/// Validates: Requirements 8.1-8.10
struct PracticeSuggestion: Codable, Identifiable {
    let id: UUID
    let issue: IssueType
    let drill: String
    let description: String
    
    init(
        id: UUID = UUID(),
        issue: IssueType,
        drill: String,
        description: String
    ) {
        self.id = id
        self.issue = issue
        self.drill = drill
        self.description = description
    }
}

/// Complete coaching feedback package with insights and recommendations
/// Validates: Requirements 8.1-8.10
struct CoachingFeedback: Codable {
    let insights: [CoachingInsight]
    let practiceSuggestions: [PracticeSuggestion]
    let quickTips: [String]
    let nextSessionFocus: [String]
    
    init(
        insights: [CoachingInsight],
        practiceSuggestions: [PracticeSuggestion],
        quickTips: [String],
        nextSessionFocus: [String]
    ) {
        self.insights = insights
        self.practiceSuggestions = practiceSuggestions
        self.quickTips = quickTips
        self.nextSessionFocus = nextSessionFocus
    }
}
