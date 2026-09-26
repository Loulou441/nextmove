//
//  GameRecording.swift
//  nextmove
//

import Foundation
import SwiftUI

struct GameRecording: Identifiable, Codable {
    let id: UUID
    var title: String
    var date: Date
    /// Only the file NAME is persisted (e.g. "ABC123.mov"), never an absolute URL.
    /// The iOS app sandbox container path changes between launches/reinstalls, so a
    /// stored absolute URL becomes invalid ("Video file not found"). We rebuild the
    /// URL against the CURRENT Documents directory every time via `videoURL`.
    var videoFileName: String?
    var thumbnailData: Data?
    var duration: TimeInterval
    var status: ProcessingStatus
    var analysis: GameAnalysis?
    var sportType: SportType

    /// Absolute URL to the video, resolved against the current Documents directory.
    /// Setting it stores just the last path component (the file name).
    var videoURL: URL? {
        get {
            guard let name = videoFileName else { return nil }
            return Self.documentsDirectory.appendingPathComponent(name)
        }
        set {
            videoFileName = newValue?.lastPathComponent
        }
    }

    /// Current app Documents directory (stable folder, path prefix may change between runs).
    static var documentsDirectory: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    }
    
    enum ProcessingStatus: String, Codable {
        case pending
        case processing
        case completed
        case failed
    }
    
    init(id: UUID = UUID(), title: String, date: Date = Date(), videoURL: URL? = nil, duration: TimeInterval = 0, sportType: SportType = .pickleball) {
        self.id = id
        self.title = title
        self.date = date
        self.videoFileName = videoURL?.lastPathComponent
        self.duration = duration
        self.status = .pending
        self.sportType = sportType
    }
    
    // Custom decoder to handle legacy recordings (old absolute videoURL, missing sportType)
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(UUID.self, forKey: .id)
        title = try container.decode(String.self, forKey: .title)
        date = try container.decode(Date.self, forKey: .date)
        thumbnailData = try container.decodeIfPresent(Data.self, forKey: .thumbnailData)
        duration = try container.decode(TimeInterval.self, forKey: .duration)
        status = try container.decode(ProcessingStatus.self, forKey: .status)
        analysis = try container.decodeIfPresent(GameAnalysis.self, forKey: .analysis)

        // Prefer the new videoFileName; migrate legacy records that stored a full URL
        // by keeping only its file name (resolved against the current Documents dir).
        if let name = try container.decodeIfPresent(String.self, forKey: .videoFileName) {
            videoFileName = name
        } else if let legacyURL = try container.decodeIfPresent(URL.self, forKey: .videoURL) {
            videoFileName = legacyURL.lastPathComponent
        } else {
            videoFileName = nil
        }

        // Migration logic: default to .pickleball for legacy recordings
        sportType = try container.decodeIfPresent(SportType.self, forKey: .sportType) ?? .pickleball
    }

    // Encode only videoFileName going forward (not the volatile absolute URL).
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encode(title, forKey: .title)
        try container.encode(date, forKey: .date)
        try container.encodeIfPresent(videoFileName, forKey: .videoFileName)
        try container.encodeIfPresent(thumbnailData, forKey: .thumbnailData)
        try container.encode(duration, forKey: .duration)
        try container.encode(status, forKey: .status)
        try container.encodeIfPresent(analysis, forKey: .analysis)
        try container.encode(sportType, forKey: .sportType)
    }
    
    private enum CodingKeys: String, CodingKey {
        case id, title, date, videoURL, videoFileName, thumbnailData, duration, status, analysis, sportType
    }
}

struct GameAnalysis: Codable {
    var overallRating: Double
    var skillRatings: SkillRatings
    var statistics: GameStatistics
    var highlights: [Highlight]
    var heatMap: CourtHeatMap?
    
    struct SkillRatings: Codable {
        var serve: Double
        var `return`: Double
        var thirdShot: Double
        var dinking: Double
        var volleys: Double
        var movement: Double
    }
    
    struct GameStatistics: Codable {
        var totalRallies: Int
        var longestRally: Int
        var winners: Int
        var errors: Int
        var attacksAttempted: Int
        var attacksSuccessful: Int
        var courtCoveragePercent: Double
    }
    
    struct Highlight: Identifiable, Codable {
        let id: UUID
        var type: HighlightType
        var timestamp: TimeInterval
        var duration: TimeInterval
        var description: String
        
        enum HighlightType: String, Codable {
            case winner
            case longRally
            case attack
            case greatDefense
            case error
        }
        
        init(id: UUID = UUID(), type: HighlightType, timestamp: TimeInterval, duration: TimeInterval, description: String) {
            self.id = id
            self.type = type
            self.timestamp = timestamp
            self.duration = duration
            self.description = description
        }
    }
    
    struct CourtHeatMap: Codable {
        var positions: [CourtPosition]
        
        struct CourtPosition: Codable {
            var x: Double
            var y: Double
            var intensity: Double
        }
    }
}
