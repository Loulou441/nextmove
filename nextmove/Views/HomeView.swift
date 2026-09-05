//
//  HomeView.swift
//  nextmove
//

import SwiftUI

struct HomeView: View {
    @EnvironmentObject var viewModel: RecordingViewModel
    @EnvironmentObject var sportManager: SportManager
    @State private var showingRecordSheet = false
    @State private var showingImportPicker = false
    
    var body: some View {
        NavigationStack {
            ZStack {
                if viewModel.recordings.isEmpty {
                    emptyStateView
                } else {
                    recordingsList
                }
            }
            .navigationTitle("NextMove")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Menu {
                        Button {
                            showingRecordSheet = true
                        } label: {
                            Label("Record Game", systemImage: "video.fill")
                        }
                        
                        Button {
                            showingImportPicker = true
                        } label: {
                            Label("Import Video", systemImage: "square.and.arrow.down")
                        }
                    } label: {
                        Image(systemName: "plus.circle.fill")
                            .font(.title2)
                    }
                }
            }
            .sheet(isPresented: $showingRecordSheet) {
                RecordingView(viewModel: viewModel, sportType: sportManager.currentSport ?? .pickleball)
            }
            .sheet(isPresented: $showingImportPicker) {
                VideoImportView(viewModel: viewModel)
            }
        }
    }
    
    private var emptyStateView: some View {
        VStack(spacing: 20) {
            Image(systemName: "video.badge.checkmark")
                .font(.system(size: 80))
                .foregroundStyle(.secondary)
            
            Text("No Recordings Yet")
                .font(.title2)
                .fontWeight(.semibold)
            
            Text("Record or import a game to get AI-powered insights")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
            
            Button {
                showingRecordSheet = true
            } label: {
                Label("Record Your First Game", systemImage: "video.fill")
                    .font(.headline)
                    .padding()
                    .background(Color.accentColor)
                    .foregroundStyle(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
            }
            .padding(.top)
        }
    }
    
    private var recordingsList: some View {
        ScrollView {
            LazyVStack(spacing: 16) {
                ForEach(viewModel.recordings) { recording in
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
