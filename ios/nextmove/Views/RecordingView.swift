//
//  RecordingView.swift
//  nextmove
//

import SwiftUI
import AVFoundation

struct RecordingView: View {
    @ObservedObject var viewModel: RecordingViewModel
    let sportType: SportType
    @Environment(\.dismiss) private var dismiss
    @State private var isRecording = false
    @State private var recordingTime: TimeInterval = 0
    @State private var timer: Timer?
    @State private var showingSaveSheet = false
    @State private var gameTitle = ""
    @State private var isPaused = false
    
    var body: some View {
        NavigationStack {
            ZStack {
                Color.black.ignoresSafeArea()
                
                VStack(spacing: 0) {
                    cameraPreviewPlaceholder
                    
                    controlsSection
                }
            }
            .navigationTitle("Record Game")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        if isRecording {
                            stopRecording()
                        }
                        dismiss()
                    }
                    .foregroundStyle(.white)
                }
                
                ToolbarItem(placement: .principal) {
                    if isRecording {
                        HStack(spacing: 8) {
                            Circle()
                                .fill(Color.red)
                                .frame(width: 8, height: 8)
                            Text("REC")
                                .font(.caption)
                                .fontWeight(.bold)
                                .foregroundStyle(.white)
                        }
                    }
                }
            }
            .sheet(isPresented: $showingSaveSheet) {
                SaveRecordingView(gameTitle: $gameTitle, duration: recordingTime) {
                    saveRecording()
                }
            }
        }
    }
    
    private var cameraPreviewPlaceholder: some View {
        GeometryReader { geometry in
            ZStack {
                Rectangle()
                    .fill(Color.gray.opacity(0.3))
                
                VStack(spacing: 16) {
                    Image(systemName: "video.fill")
                        .font(.system(size: 70))
                        .foregroundStyle(.white.opacity(0.7))
                    
                    Text("Camera Preview")
                        .font(.headline)
                        .foregroundStyle(.white.opacity(0.7))
                    
                    if isRecording {
                        Text(formatTime(recordingTime))
                            .font(.system(size: 48, weight: .bold, design: .rounded))
                            .foregroundStyle(.white)
                            .padding(.top, 8)
                            .monospacedDigit()
                    }
                    
                    Text("Position camera to capture full court")
                        .font(.caption)
                        .foregroundStyle(.white.opacity(0.6))
                        .padding(.top, 4)
                }
                
                // Grid overlay for alignment
                if !isRecording {
                    GridOverlay()
                        .stroke(Color.white.opacity(0.3), lineWidth: 1)
                }
            }
        }
    }
    
    private var controlsSection: some View {
        VStack(spacing: 24) {
            if isRecording {
                recordingControls
            } else {
                startButton
            }
            
            tipsSection
        }
        .padding(.vertical, 32)
        .background(Color.black.opacity(0.8))
    }
    
    private var startButton: some View {
        Button {
            startRecording()
        } label: {
            ZStack {
                Circle()
                    .stroke(Color.white, lineWidth: 4)
                    .frame(width: 80, height: 80)
                
                Circle()
                    .fill(Color.red)
                    .frame(width: 64, height: 64)
            }
        }
    }
    
    private var recordingControls: some View {
        HStack(spacing: 50) {
            Button {
                stopRecording()
            } label: {
                ZStack {
                    Circle()
                        .fill(Color.white.opacity(0.2))
                        .frame(width: 60, height: 60)
                    
                    RoundedRectangle(cornerRadius: 4)
                        .fill(Color.white)
                        .frame(width: 24, height: 24)
                }
            }
            
            ZStack {
                Circle()
                    .stroke(Color.white, lineWidth: 4)
                    .frame(width: 80, height: 80)
                
                Circle()
                    .fill(Color.red)
                    .frame(width: 64, height: 64)
            }
        }
    }
    
    private var tipsSection: some View {
        VStack(spacing: 8) {
            HStack(spacing: 12) {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundStyle(.green)
                Text("Mount camera 4+ feet high")
                    .font(.caption)
                    .foregroundStyle(.white.opacity(0.8))
                Spacer()
            }
            
            HStack(spacing: 12) {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundStyle(.green)
                Text("Ensure all court corners are visible")
                    .font(.caption)
                    .foregroundStyle(.white.opacity(0.8))
                Spacer()
            }
        }
        .padding(.horizontal, 32)
    }
    
    private func startRecording() {
        isRecording = true
        recordingTime = 0
        timer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { _ in
            recordingTime += 1
        }
    }
    
    private func stopRecording() {
        isRecording = false
        timer?.invalidate()
        timer = nil
        if recordingTime > 0 {
            showingSaveSheet = true
        }
    }
    
    private func saveRecording() {
        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let videoURL = documentsPath.appendingPathComponent("\(UUID().uuidString).mov")
        
        viewModel.addRecording(videoURL: videoURL, title: gameTitle.isEmpty ? "Game Recording" : gameTitle, sportType: sportType)
        dismiss()
    }
    
    private func formatTime(_ time: TimeInterval) -> String {
        let hours = Int(time) / 3600
        let minutes = (Int(time) % 3600) / 60
        let seconds = Int(time) % 60
        
        if hours > 0 {
            return String(format: "%d:%02d:%02d", hours, minutes, seconds)
        } else {
            return String(format: "%02d:%02d", minutes, seconds)
        }
    }
}

struct GridOverlay: Shape {
    func path(in rect: CGRect) -> Path {
        var path = Path()
        
        // Vertical lines
        let verticalSpacing = rect.width / 3
        for i in 1..<3 {
            let x = CGFloat(i) * verticalSpacing
            path.move(to: CGPoint(x: x, y: 0))
            path.addLine(to: CGPoint(x: x, y: rect.height))
        }
        
        // Horizontal lines
        let horizontalSpacing = rect.height / 3
        for i in 1..<3 {
            let y = CGFloat(i) * horizontalSpacing
            path.move(to: CGPoint(x: 0, y: y))
            path.addLine(to: CGPoint(x: rect.width, y: y))
        }
        
        return path
    }
}

struct SaveRecordingView: View {
    @Binding var gameTitle: String
    let duration: TimeInterval
    let onSave: () -> Void
    @Environment(\.dismiss) private var dismiss
    @FocusState private var isTitleFocused: Bool
    
    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("e.g., Tournament Finals", text: $gameTitle)
                        .focused($isTitleFocused)
                } header: {
                    Text("Game Title")
                } footer: {
                    Text("Give your recording a memorable name")
                }
                
                Section {
                    HStack {
                        Text("Duration")
                        Spacer()
                        Text(formatDuration(duration))
                            .foregroundStyle(.secondary)
                    }
                } header: {
                    Text("Recording Info")
                }
            }
            .navigationTitle("Save Recording")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        onSave()
                        dismiss()
                    }
                    .fontWeight(.semibold)
                }
            }
            .onAppear {
                isTitleFocused = true
            }
        }
    }
    
    private func formatDuration(_ duration: TimeInterval) -> String {
        let minutes = Int(duration) / 60
        let seconds = Int(duration) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}
