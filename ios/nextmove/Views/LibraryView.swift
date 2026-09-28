//
//  LibraryView.swift
//  nextmove
//
//  Created by Asmae  on 09/03/2026.
//

import SwiftUI

struct LibraryView: View {
    @EnvironmentObject var viewModel: RecordingViewModel
    @EnvironmentObject var sportManager: SportManager

    @State private var showComparison = false

    private var filteredRecordings: [GameRecording] {
        guard let sport = sportManager.currentSport else { return [] }
        return viewModel.recordings(for: sport)
    }

    /// Matchs déjà analysés du sport courant : seuls ceux-ci sont comparables.
    private var analyzedRecordings: [GameRecording] {
        filteredRecordings.filter { $0.status == .completed && $0.analysis != nil }
    }

    private var canCompare: Bool { analyzedRecordings.count >= 2 }

    var body: some View {
        NavigationStack {
            ZStack {
                if filteredRecordings.isEmpty {
                    emptyStateView
                } else {
                    recordingsList
                }
            }
            .navigationTitle("Library")
            .toolbar {
                if canCompare {
                    ToolbarItem(placement: .primaryAction) {
                        Button {
                            showComparison = true
                        } label: {
                            Label("Comparer", systemImage: "square.on.square")
                        }
                    }
                }
            }
            .sheet(isPresented: $showComparison) {
                MatchComparisonView(recordings: analyzedRecordings)
            }
        }
    }
    
    private var emptyStateView: some View {
        VStack(spacing: 20) {
            Text(sportManager.currentSport?.icon ?? "")
                .font(.system(size: 80))
            
            Text("No \(sportManager.currentSport?.displayName ?? "") Recordings")
                .font(.title2)
                .fontWeight(.semibold)
            
            Text("Go to the Upload tab to record your first game")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
        }
    }
    
    private var recordingsList: some View {
        ScrollView {
            LazyVStack(spacing: 16) {
                ForEach(filteredRecordings) { recording in
                    NavigationLink(destination: AnalysisDetailView(recording: recording, viewModel: viewModel)) {
                        RecordingCard(recording: recording, viewModel: viewModel)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding()
        }
    }
}
