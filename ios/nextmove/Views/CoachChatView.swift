//
//  CoachChatView.swift
//  nextmove
//
//  Conversational AI coach screen. Chat with a coach that gives personalized
//  recommendations based on your game analysis.
//

import SwiftUI

struct CoachChatView: View {
    @StateObject private var viewModel: CoachChatViewModel
    let sportType: SportType

    init(sportType: SportType, analysis: GameAnalysis?, feedback: CoachingFeedback? = nil) {
        self.sportType = sportType
        _viewModel = StateObject(wrappedValue: CoachChatViewModel(
            sportType: sportType,
            analysis: analysis,
            feedback: feedback
        ))
    }

    var body: some View {
        VStack(spacing: 0) {
            messagesList
            suggestedPromptsBar
            inputBar
        }
        .background(Color(.systemGroupedBackground))
        .navigationTitle("AI Coach")
        .navigationBarTitleDisplayMode(.inline)
    }

    private var messagesList: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(spacing: 12) {
                    ForEach(viewModel.messages) { message in
                        MessageBubble(message: message, accent: sportType.color)
                            .id(message.id)
                    }

                    if viewModel.isThinking {
                        HStack {
                            TypingIndicator(accent: sportType.color)
                            Spacer()
                        }
                        .id("typing")
                    }
                }
                .padding()
            }
            .onChange(of: viewModel.messages.count) { _, _ in
                scrollToBottom(proxy)
            }
            .onChange(of: viewModel.isThinking) { _, thinking in
                if thinking { withAnimation { proxy.scrollTo("typing", anchor: .bottom) } }
            }
        }
    }

    private func scrollToBottom(_ proxy: ScrollViewProxy) {
        guard let last = viewModel.messages.last else { return }
        withAnimation { proxy.scrollTo(last.id, anchor: .bottom) }
    }

    private var suggestedPromptsBar: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(viewModel.suggestedPrompts, id: \.self) { prompt in
                    Button {
                        viewModel.sendSuggested(prompt)
                    } label: {
                        Text(prompt)
                            .font(.caption)
                            .fontWeight(.medium)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 8)
                            .background(sportType.color.opacity(0.12))
                            .foregroundStyle(sportType.color)
                            .clipShape(Capsule())
                    }
                    .disabled(viewModel.isThinking)
                }
            }
            .padding(.horizontal)
            .padding(.vertical, 8)
        }
    }

    private var inputBar: some View {
        HStack(spacing: 12) {
            TextField("Ask your coach...", text: $viewModel.inputText, axis: .vertical)
                .textFieldStyle(.plain)
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
                .background(Color(.systemBackground))
                .clipShape(RoundedRectangle(cornerRadius: 20))
                .lineLimit(1...4)
                .onSubmit { if viewModel.canSend { viewModel.send() } }

            Button {
                viewModel.send()
            } label: {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.system(size: 32))
                    .foregroundStyle(viewModel.canSend ? sportType.color : Color.gray.opacity(0.4))
            }
            .disabled(!viewModel.canSend)
        }
        .padding()
        .background(.ultraThinMaterial)
    }
}

// MARK: - Message Bubble

private struct MessageBubble: View {
    let message: CoachChatMessage
    let accent: Color

    private var isUser: Bool { message.role == .user }

    var body: some View {
        HStack {
            if isUser { Spacer(minLength: 40) }

            VStack(alignment: isUser ? .trailing : .leading, spacing: 4) {
                if !isUser {
                    Label("Coach", systemImage: "figure.tennis")
                        .font(.caption2)
                        .foregroundStyle(accent)
                }
                Text(message.text)
                    .font(.subheadline)
                    .foregroundStyle(isUser ? .white : .primary)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(
                        isUser
                        ? AnyView(accent)
                        : AnyView(Color(.systemBackground))
                    )
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                    .shadow(color: .black.opacity(0.05), radius: 4, y: 2)
            }

            if !isUser { Spacer(minLength: 40) }
        }
    }
}

// MARK: - Typing Indicator

private struct TypingIndicator: View {
    let accent: Color
    @State private var phase = 0.0

    var body: some View {
        HStack(spacing: 4) {
            ForEach(0..<3) { i in
                Circle()
                    .fill(accent.opacity(0.6))
                    .frame(width: 7, height: 7)
                    .scaleEffect(scale(for: i))
            }
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .onAppear {
            withAnimation(.easeInOut(duration: 0.6).repeatForever()) {
                phase = 1.0
            }
        }
    }

    private func scale(for index: Int) -> CGFloat {
        let offset = Double(index) * 0.2
        return 0.6 + 0.4 * abs(sin((phase + offset) * .pi))
    }
}

#Preview {
    NavigationStack {
        CoachChatView(sportType: .pickleball, analysis: nil)
    }
}
