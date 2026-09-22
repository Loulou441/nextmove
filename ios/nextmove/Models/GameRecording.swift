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
    var videoURL: URL?
    var thumbnailData: Data?
    var duration: TimeInterval
    var status: ProcessingStatus
    var analysis: GameAnalysis?
    var sportType: SportType
    
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
        self.videoURL = videoURL
        self.duration = duration
        self.status = .pending
        self.sportType = sportType
    }
    
    // Custom decoder to handle legacy recordings without sportType
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(UUID.self, forKey: .id)
        title = try container.decode(String.self, forKey: .title)
        date = try container.decode(Date.self, forKey: .date)
        videoURL = try container.decodeIfPresent(URL.self, forKey: .videoURL)
        thumbnailData = try container.decodeIfPresent(Data.self, forKey: .thumbnailData)
        duration = try container.decode(TimeInterval.self, forKey: .duration)
        status = try container.decode(ProcessingStatus.self, forKey: .status)
        analysis = try container.decodeIfPresent(GameAnalysis.self, forKey: .analysis)
        
        // Migration logic: default to .pickleball for legacy recordings
        sportType = try container.decodeIfPresent(SportType.self, forKey: .sportType) ?? .pickleball
    }
    
    private enum CodingKeys: String, CodingKey {
        case id, title, date, videoURL, thumbnailData, duration, status, analysis, sportType
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
