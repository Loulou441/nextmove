//
//  SportSelectionModal.swift
//  nextmove
//
//  Created by Asmae  on 09/03/2026.
//

import SwiftUI

struct SportSelectionModal: View {
    @ObservedObject var sportManager: SportManager
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 32) {
                headerSection
                sportsGrid
                Spacer()
            }
            .padding()
            .navigationTitle("")
            .navigationBarTitleDisplayMode(.inline)
            .interactiveDismissDisabled(sportManager.currentSport == nil)
        }
    }
    
    private var headerSection: some View {
        VStack(spacing: 12) {
            Text("Let's go Buddy! Choose your sport")
                .font(.title2)
                .fontWeight(.bold)
                .multilineTextAlignment(.center)
            
            Text("Select the sport you want to analyze")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .padding(.top, 32)
    }
    
    private var sportsGrid: some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 16) {
            ForEach(SportType.allCases) { sport in
                SportCard(sport: sport) {
                    sportManager.selectSport(sport)
                    dismiss()
                }
            }
        }
    }
}

struct SportCard: View {
    let sport: SportType
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 16) {
                Text(sport.icon)
                    .font(.system(size: 60))
                
                VStack(spacing: 4) {
                    Text(sport.displayName)
                        .font(.headline)
                        .foregroundStyle(.primary)
                    
                    Text(sport.description)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                }
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 24)
            .background(sport.color.opacity(0.1))
            .clipShape(RoundedRectangle(cornerRadius: 16))
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(sport.color, lineWidth: 2)
            )
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    SportSelectionModal(sportManager: SportManager())
}
