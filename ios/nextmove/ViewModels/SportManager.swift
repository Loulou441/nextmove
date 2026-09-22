//
//  SportManager.swift
//  nextmove
//
//  Created by Asmae  on 09/03/2026.
//

import SwiftUI
import Combine

@MainActor
class SportManager: ObservableObject {
    @AppStorage("selectedSport") private var storedSport: String = ""
    @Published var currentSport: SportType?
    @Published var showSportSelection: Bool = false
    
    init() {
        loadSport()
    }
    
    private func loadSport() {
        if let sport = SportType(rawValue: storedSport) {
            currentSport = sport
        } else {
            // First launch or invalid stored value - show sport selection
            showSportSelection = true
        }
    }
    
    func selectSport(_ sport: SportType) {
        currentSport = sport
        storedSport = sport.rawValue
        showSportSelection = false
    }
    
    func requestSportChange() {
        showSportSelection = true
    }
}
