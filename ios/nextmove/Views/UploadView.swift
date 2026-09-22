//
//  UploadView.swift
//  nextmove
//
//  Created by Asmae  on 09/03/2026.
//

import SwiftUI

struct UploadView: View {
    @EnvironmentObject var viewModel: RecordingViewModel
    @EnvironmentObject var sportManager: SportManager
    @State private var showingRecordSheet = false
    @State private var showingImportSheet = false
    @State private var showImportSuccess = false
    @State private var recordingsCountBeforeImport = 0
    
    var body: some View {
        NavigationStack {
            ZStack {
                Color(.systemGroupedBackground)
                    .ignoresSafeArea()
                
                VStack(spacing: 32) {
                    sportIndicator
                    instructionsSection
                    uploadButton
                    tipsSection
                    Spacer()
                }
                .padding()
                
                // Success toast overlay
                if showImportSuccess {
                    VStack {
                        Spacer()
                        HStack {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundStyle(.green)
                            Text("Video imported successfully!")
                                .font(.subheadline)
                                .fontWeight(.medium)
                        }
                        .padding()
                        .background(Color(.systemBackground))
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                        .shadow(radius: 10)
                        .padding()
                    }
                    .transition(.move(edge: .bottom).combined(with: .opacity))
                    .animation(.spring(), value: showImportSuccess)
                }
            }
            .navigationTitle("Upload")
            .sheet(isPresented: $showingRecordSheet) {
                RecordingView(viewModel: viewModel, sportType: sportManager.currentSport ?? .pickleball)
            }
            .sheet(isPresented: $showingImportSheet) {
                VideoImportView(viewModel: viewModel)
            }
            .onChange(of: showingImportSheet) { oldValue, newValue in
                if !oldValue && newValue {
                    // Store count before import
                    recordingsCountBeforeImport = viewModel.recordings.count
                } else if oldValue && !newValue {
                    // Check if a new recording was added
                    if viewModel.recordings.count > recordingsCountBeforeImport {
                        showImportSuccess = true
                        // Hide toast after 2 seconds
                        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                            withAnimation {
                                showImportSuccess = false
                            }
                        }
                    }
                }
            }
        }
    }
    
    private var sportIndicator: some View {
        HStack(spacing: 12) {
            Text(sportManager.currentSport?.icon ?? "")
                .font(.title)
            Text("Recording \(sportManager.currentSport?.displayName ?? "")")
                .font(.headline)
                .foregroundStyle(.secondary)
        }
        .padding()
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
    
    private var instructionsSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("How to Record")
                .font(.title3)
                .fontWeight(.semibold)
            
            InstructionRow(number: 1, text: "Position your camera to capture the full court")
            InstructionRow(number: 2, text: "Mount camera 4+ feet high for best results")
            InstructionRow(number: 3, text: "Tap the button below to start recording")
        }
        .padding()
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 16))
    }
    
    private var uploadButton: some View {
        VStack(spacing: 16) {
            Button {
                showingRecordSheet = true
            } label: {
                HStack {
                    Image(systemName: "video.fill")
                        .font(.title3)
                    Text("Record Video")
                        .font(.headline)
                }
                .foregroundStyle(.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 18)
                .background(Color.green)
                .clipShape(RoundedRectangle(cornerRadius: 14))
                .shadow(color: .green.opacity(0.3), radius: 8, y: 4)
            }
            
            Button {
                showingImportSheet = true
            } label: {
                HStack {
                    Image(systemName: "square.and.arrow.down")
                        .font(.title3)
                    Text("Import Video")
                        .font(.headline)
                }
                .foregroundStyle(.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 18)
                .background(Color.blue)
                .clipShape(RoundedRectangle(cornerRadius: 14))
                .shadow(color: .blue.opacity(0.3), radius: 8, y: 4)
            }
        }
    }
    
    private var tipsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Pro Tips")
                .font(.subheadline)
                .fontWeight(.semibold)
                .foregroundStyle(.secondary)
            
            TipRow(icon: "checkmark.circle.fill", text: "Record in landscape mode")
            TipRow(icon: "checkmark.circle.fill", text: "Ensure good lighting")
            TipRow(icon: "checkmark.circle.fill", text: "Keep camera stable")
        }
    }
}

struct TipRow: View {
    let icon: String
    let text: String
    
    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: icon)
                .foregroundStyle(.green)
                .font(.caption)
            Text(text)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }
}

struct InstructionRow: View {
    let number: Int
    let text: String
    
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Text("\(number)")
                .font(.headline)
                .foregroundStyle(.white)
                .frame(width: 28, height: 28)
                .background(Color.green)
                .clipShape(Circle())
            
            Text(text)
                .font(.subheadline)
                .foregroundStyle(.primary)
        }
    }
}
