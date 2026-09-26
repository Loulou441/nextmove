//
//  ContentView.swift
//  nextmove
//
//  Created by Asmae ‎ on 09/03/2026.
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject private var api: NextMoveAPI
    @StateObject private var viewModel = RecordingViewModel()
    @StateObject private var sportManager = SportManager()
    
    var body: some View {
        TabView {
            MeView()
                .environmentObject(viewModel)
                .environmentObject(sportManager)
                .tabItem {
                    Label("Me", systemImage: "person.fill")
                }
            
            LibraryView()
                .environmentObject(viewModel)
                .environmentObject(sportManager)
                .tabItem {
                    Label("Library", systemImage: "books.vertical.fill")
                }
            
            UploadView()
                .environmentObject(viewModel)
                .environmentObject(sportManager)
                .tabItem {
                    Label("Upload", systemImage: "arrow.up.circle.fill")
                }
        }
        .tint(.green)
        .sheet(isPresented: $sportManager.showSportSelection) {
            SportSelectionModal(sportManager: sportManager)
        }
        // Donne au ViewModel accès à l'API partagée pour synchroniser les
        // analyses terminées vers la base (visibles ensuite sur le web).
        .onAppear { viewModel.api = api }
    }
}

#Preview {
    ContentView()
}
