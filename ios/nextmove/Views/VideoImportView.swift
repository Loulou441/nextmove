//
//  VideoImportView.swift
//  nextmove
//

import SwiftUI
import PhotosUI

struct VideoImportView: View {
    @ObservedObject var viewModel: RecordingViewModel
    @EnvironmentObject var sportManager: SportManager
    @Environment(\.dismiss) private var dismiss
    @State private var selectedItem: PhotosPickerItem?
    @State private var gameTitle = ""
    @State private var isImporting = false
    @State private var showError = false
    @State private var errorMessage = ""
    
    var body: some View {
        NavigationStack {
            Form {
                Section {
                    HStack {
                        Text(sportManager.currentSport?.icon ?? "🎾")
                            .font(.title2)
                        Text(sportManager.currentSport?.displayName ?? "Sport")
                            .font(.headline)
                        Spacer()
                    }
                } header: {
                    Text("Sport")
                }
                
                Section {
                    TextField("Game Title", text: $gameTitle)
                        .disabled(isImporting)
                } header: {
                    Text("Recording Details")
                }
                
                Section {
                    PhotosPicker(selection: $selectedItem, matching: .videos) {
                        HStack {
                            Image(systemName: "photo.on.rectangle")
                                .foregroundStyle(.blue)
                            Text(selectedItem == nil ? "Select Video" : "Video Selected")
                            Spacer()
                            if selectedItem != nil {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundStyle(.green)
                            }
                        }
                    }
                    .disabled(isImporting)
                } header: {
                    Text("Video File")
                } footer: {
                    Text("Select a video from your photo library to analyze")
                }
                
                if isImporting {
                    Section {
                        HStack {
                            ProgressView()
                            Text("Importing video...")
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }
            .navigationTitle("Import Video")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                    .disabled(isImporting)
                }
                
                ToolbarItem(placement: .confirmationAction) {
                    Button("Import") {
                        importVideo()
                    }
                    .disabled(selectedItem == nil || isImporting)
                }
            }
            .alert("Import Failed", isPresented: $showError) {
                Button("OK", role: .cancel) { }
            } message: {
                Text(errorMessage)
            }
        }
    }
    
    private func importVideo() {
        guard let selectedItem else { return }
        
        isImporting = true
        
        Task {
            do {
                guard let data = try await selectedItem.loadTransferable(type: Data.self) else {
                    await MainActor.run {
                        errorMessage = "Failed to load video data"
                        showError = true
                        isImporting = false
                    }
                    return
                }
                
                let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
                let videoURL = documentsPath.appendingPathComponent("\(UUID().uuidString).mov")
                
                try data.write(to: videoURL)
                
                await MainActor.run {
                    let title = gameTitle.isEmpty ? "Imported \(sportManager.currentSport?.displayName ?? "Game")" : gameTitle
                    let sport = sportManager.currentSport ?? .pickleball
                    viewModel.addRecording(videoURL: videoURL, title: title, sportType: sport)
                    isImporting = false
                }
                
                // Small delay to ensure UI updates before dismissing
                try? await Task.sleep(nanoseconds: 100_000_000) // 0.1 seconds
                
                await MainActor.run {
                    dismiss()
                }
            } catch {
                await MainActor.run {
                    errorMessage = "Failed to import video: \(error.localizedDescription)"
                    showError = true
                    isImporting = false
                }
            }
        }
    }
}
