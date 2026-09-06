//
//  MeView.swift
//  nextmove
//
//  Created by Asmae  on 09/03/2026.
//

import SwiftUI

struct MeView: View {
    @EnvironmentObject var viewModel: RecordingViewModel
    @EnvironmentObject var sportManager: SportManager
    
    private var filteredRecordings: [GameRecording] {
        guard let sport = sportManager.currentSport else { return [] }
        return viewModel.recordings(for: sport)
    }
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    profileSection
                    
                    if !filteredRecordings.isEmpty {
                        progressSection
                    }
                    
                    settingsSection
                }
                .padding()
            }
            .navigationTitle("Me")
        }
    }
    
    private var profileSection: some View {
        VStack(spacing: 16) {
            Image(systemName: "person.circle.fill")
                .font(.system(size: 80))
                .foregroundStyle(.green)
            
            Text("Player Profile")
                .font(.title2)
                .fontWeight(.bold)
            
            HStack(spacing: 12) {
                Text(sportManager.currentSport?.icon ?? "")
                    .font(.title3)
                Text(sportManager.currentSport?.displayName ?? "")
                    .font(.headline)
                    .foregroundStyle(.secondary)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
            .background(Color(.secondarySystemBackground))
            .clipShape(RoundedRectangle(cornerRadius: 8))
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 24)
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 16))
    }
    
    private var progressSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Progress")
                .font(.title3)
                .fontWeight(.semibold)
            
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                ProgressCard(
                    title: "Average Rating",
                    value: String(format: "%.1f", calculateAverageRating()),
                    trend: "+0.3",
                    icon: "star.fill",
                    color: .green
                )
                ProgressCard(
                    title: "Games Analyzed",
                    value: "\(completedGamesCount)",
                    trend: "+\(completedGamesCount)",
                    icon: "video.fill",
                    color: .orange
                )
            }
            
            NavigationLink {
                DetailedProgressView(recordings: filteredRecordings)
            } label: {
                Text("View Detailed Stats")
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundStyle(.green)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.green.opacity(0.1))
                    .clipShape(RoundedRectangle(cornerRadius: 12))
            }
        }
    }
    
    private var completedGamesCount: Int {
        filteredRecordings.filter { $0.status == .completed }.count
    }
    
    private func calculateAverageRating() -> Double {
        let completed = filteredRecordings.filter { $0.status == .completed && $0.analysis != nil }
        guard !completed.isEmpty else { return 0.0 }
        let sum = completed.compactMap { $0.analysis?.overallRating }.reduce(0, +)
        return sum / Double(completed.count)
    }
    
    private var settingsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Settings")
                .font(.title3)
                .fontWeight(.semibold)
            
            NavigationLink {
                SettingsView()
                    .environmentObject(sportManager)
            } label: {
                SettingsRow(icon: "gearshape.fill", title: "App Settings", color: .gray)
            }
            
            Button {
                sportManager.requestSportChange()
            } label: {
                SettingsRow(icon: "sportscourt.fill", title: "Change Sport", color: .green)
            }
        }
    }
}

struct SettingsRow: View {
    let icon: String
    let title: String
    let color: Color
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .foregroundStyle(color)
                .frame(width: 24)
            
            Text(title)
                .foregroundStyle(.primary)
            
            Spacer()
            
            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding()
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}
