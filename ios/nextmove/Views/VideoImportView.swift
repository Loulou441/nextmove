//
//  VideoImportView.swift
//  nextmove
//

import SwiftUI
import PhotosUI
import UniformTypeIdentifiers
import CoreTransferable

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
                // `PhotosPickerItem` only exposes `loadTransferable(type:)` — it has
                // no `loadFileRepresentation` (that belongs to NSItemProvider). We
                // load the video as a FILE via a small `Transferable` wrapper
                // (`ImportedVideo`) that copies the picker's temporary file into our
                // own container. This works for HEVC/H.265 and iCloud videos and
                // doesn't load the whole video into memory the way `Data` would.
                guard let imported = try await selectedItem.loadTransferable(type: ImportedVideo.self) else {
                    await MainActor.run {
                        errorMessage = String(localized: "Impossible de lire le format de cette vidéo.")
                        showError = true
                        isImporting = false
                    }
                    return
                }

                let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
                let destURL = documentsPath.appendingPathComponent("\(UUID().uuidString).mov")

                // Move the transfer's copied file to its final name in Documents.
                if FileManager.default.fileExists(atPath: destURL.path) {
                    try FileManager.default.removeItem(at: destURL)
                }
                try FileManager.default.moveItem(at: imported.url, to: destURL)
                let videoURL = destURL

                await MainActor.run {
                    let title = gameTitle.isEmpty
                        ? "Imported \(sportManager.currentSport?.displayName ?? "Game")"
                        : gameTitle
                    let sport = sportManager.currentSport ?? .pickleball
                    viewModel.addRecording(videoURL: videoURL, title: title, sportType: sport)
                    isImporting = false
                }

                try? await Task.sleep(nanoseconds: 100_000_000)
                await MainActor.run { dismiss() }

            } catch {
                await MainActor.run {
                    errorMessage = String(localized: "Échec de l'import : \(error.localizedDescription)")
                    showError = true
                    isImporting = false
                }
            }
        }
    }
}

/// A video loaded from the photo library as a FILE (not raw `Data`).
///
/// `PhotosPickerItem.loadTransferable(type: ImportedVideo.self)` triggers the
/// `importing` closure below with a temporary URL that the system owns and may
/// delete as soon as the closure returns. We immediately copy it into the app's
/// temporary directory and hand back a URL we control, which the caller then
/// moves into Documents. This mirrors the file-based import Apple recommends for
/// large media (HEVC / iCloud-backed) and avoids loading the whole clip into RAM.
struct ImportedVideo: Transferable {
    let url: URL

    static var transferRepresentation: some TransferRepresentation {
        FileRepresentation(importedContentType: .movie) { received in
            let copy = FileManager.default.temporaryDirectory
                .appendingPathComponent(UUID().uuidString)
                .appendingPathExtension(received.file.pathExtension.isEmpty ? "mov" : received.file.pathExtension)
            if FileManager.default.fileExists(atPath: copy.path) {
                try FileManager.default.removeItem(at: copy)
            }
            try FileManager.default.copyItem(at: received.file, to: copy)
            return ImportedVideo(url: copy)
        }
    }
}
