//
//  SettingsView.swift
//  nextmove
//
//  Created by Asmae  on 09/03/2026.
//

import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var sportManager: SportManager
    
    var body: some View {
        NavigationStack {
            List {
                Section {
                    HStack {
                        Text("Current Sport")
                        Spacer()
                        HStack(spacing: 8) {
                            Text(sportManager.currentSport?.icon ?? "")
                            Text(sportManager.currentSport?.displayName ?? "")
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                
                Section {
                    Button {
                        sportManager.requestSportChange()
                    } label: {
                        HStack {
                            Image(systemName: "sportscourt.fill")
                                .foregroundStyle(.green)
                            Text("Change Sport")
                                .foregroundStyle(.primary)
                        }
                    }
                }
                
                Section("About") {
                    HStack {
                        Text("Version")
                        Spacer()
                        Text("1.0.0")
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}
