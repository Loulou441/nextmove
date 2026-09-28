//
//  SettingsView.swift
//  nextmove
//
//  Created by Asmae  on 09/03/2026.
//

import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var sportManager: SportManager
    @EnvironmentObject var languageManager: LanguageManager
    
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

                Section {
                    Picker(selection: languageBinding) {
                        ForEach(AppLanguage.allCases) { language in
                            Text(language.displayName).tag(language)
                        }
                    } label: {
                        HStack {
                            Image(systemName: "globe")
                                .foregroundStyle(.green)
                            Text("settings.language")
                        }
                    }
                } footer: {
                    Text("settings.language.footer")
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

    /// Bridges the picker to LanguageManager so a change persists and re-renders
    /// the whole app immediately.
    private var languageBinding: Binding<AppLanguage> {
        Binding(
            get: { languageManager.current },
            set: { languageManager.select($0) }
        )
    }
}
