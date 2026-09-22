//
//  DetailedProgressView.swift
//  nextmove
//
//  Created by Asmae  on 09/03/2026.
//

import SwiftUI

struct DetailedProgressView: View {
    let recordings: [GameRecording]
    
    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                Text("Detailed Statistics")
                    .font(.title2)
                    .fontWeight(.bold)
                
                Text("Coming soon...")
                    .foregroundStyle(.secondary)
            }
            .padding()
        }
        .navigationTitle("Detailed Stats")
        .navigationBarTitleDisplayMode(.inline)
    }
}
