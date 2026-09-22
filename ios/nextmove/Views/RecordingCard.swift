//
//  RecordingCard.swift
//  nextmove
//

import SwiftUI

struct RecordingCard: View {
    let recording: GameRecording
    @ObservedObject var viewModel: RecordingViewModel
    @State private var showingDeleteAlert = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(recording.title)
                        .font(.headline)
                        .foregroundStyle(.primary)
                    
                    HStack(spacing: 8) {
                        // Sport type indicator
                        HStack(spacing: 4) {
                            Text(recording.sportType.icon)
                                .font(.caption)
                            Text(recording.sportType.displayName)
                                .font(.caption)
                                .foregroundStyle(recording.sportType.color)
                        }
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(recording.sportType.color.opacity(0.15))
                        .clipShape(RoundedRectangle(cornerRadius: 4))
                        
                        Text(recording.date.formatted(date: .abbreviated, time: .shortened))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        
                        if recording.duration > 0 {
                            Text("•")
                                .foregroundStyle(.secondary)
                            Text(formatDuration(recording.duration))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                
                Spacer()
                
                Menu {
                    if recording.status == .pending {
                        Button {
                            let recordingToProcess = recording
                            Task.detached(priority: .userInitiated) { [weak viewModel] in
                                await viewModel?.processRecording(recordingToProcess)
                            }
                        } label: {
                            Label("Analyze Now", systemImage: "wand.and.stars")
                        }
                    }
                    
                    Button(role: .destructive) {
                        showingDeleteAlert = true
                    } label: {
                        Label("Delete", systemImage: "trash")
                    }
                } label: {
                    Image(systemName: "ellipsis.circle")
                        .font(.title3)
                        .foregroundStyle(.secondary)
                }
                
                statusBadge
            }
            
            if recording.status == .completed, let analysis = recording.analysis {
                Divider()
                
                HStack(spacing: 20) {
                    StatItem(title: "Rating", value: String(format: "%.1f", analysis.overallRating), icon: "star.fill", color: ratingColor(analysis.overallRating))
                    StatItem(title: "Rallies", value: "\(analysis.statistics.totalRallies)", icon: "arrow.left.arrow.right", color: .blue)
                    StatItem(title: "Winners", value: "\(analysis.statistics.winners)", icon: "checkmark.circle.fill", color: .green)
                }
            }
            
            if recording.status == .pending {
                Button {
                    let recordingToProcess = recording
                    Task.detached(priority: .userInitiated) { [weak viewModel] in
                        await viewModel?.processRecording(recordingToProcess)
                    }
                } label: {
                    HStack {
                        Image(systemName: "wand.and.stars")
                        Text("Analyze Game")
                    }
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .background(
                        LinearGradient(
                            colors: [Color.blue, Color.blue.opacity(0.8)],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .foregroundStyle(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                }
                .disabled(viewModel.isProcessing)
            }
            
            if recording.status == .processing {
                VStack(spacing: 8) {
                    ProgressView(value: viewModel.analysisProgressPercentage) {
                        HStack {
                            ProgressView()
                                .scaleEffect(0.7)
                            Text(viewModel.analysisProgress)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                    .tint(.blue)
                    
                    Text("\(Int(viewModel.analysisProgressPercentage * 100))%")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 8)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .shadow(color: .black.opacity(0.08), radius: 10, y: 4)
        .alert("Delete Recording", isPresented: $showingDeleteAlert) {
            Button("Cancel", role: .cancel) { }
            Button("Delete", role: .destructive) {
                viewModel.deleteRecording(recording)
            }
        } message: {
            Text("This will permanently delete this recording and its analysis.")
        }
    }
    
    private func formatDuration(_ duration: TimeInterval) -> String {
        let minutes = Int(duration) / 60
        let seconds = Int(duration) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
    
    private func ratingColor(_ rating: Double) -> Color {
        switch rating {
        case 4.5...: return .green
        case 3.5..<4.5: return .blue
        case 2.5..<3.5: return .orange
        default: return .red
        }
    }
    
    private var statusBadge: some View {
        Group {
            switch recording.status {
            case .pending:
                Label("Pending", systemImage: "clock")
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.orange.opacity(0.2))
                    .foregroundStyle(.orange)
                    .clipShape(Capsule())
            case .processing:
                Label("Processing", systemImage: "gearshape.fill")
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.blue.opacity(0.2))
                    .foregroundStyle(.blue)
                    .clipShape(Capsule())
            case .completed:
                Label("Ready", systemImage: "checkmark.circle.fill")
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.green.opacity(0.2))
                    .foregroundStyle(.green)
                    .clipShape(Capsule())
            case .failed:
                Label("Failed", systemImage: "xmark.circle.fill")
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.red.opacity(0.2))
                    .foregroundStyle(.red)
                    .clipShape(Capsule())
            }
        }
    }
}

struct StatItem: View {
    let title: String
    let value: String
    let icon: String
    var color: Color = .secondary
    
    var body: some View {
        VStack(spacing: 4) {
            Image(systemName: icon)
                .font(.caption)
                .foregroundStyle(color)
            Text(value)
                .font(.headline)
                .foregroundStyle(.primary)
            Text(title)
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
    }
}
