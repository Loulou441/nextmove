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

    init(sportType: SportType, analysis: GameAnalysis?, feedback: CoachingFeedback? = nil, api: NextMoveAPI? = nil, matchId: String? = nil, playerLabel: String? = nil) {
        self.sportType = sportType
        _viewModel = StateObject(wrappedValue: CoachChatViewModel(
            sportType: sportType,
            analysis: analysis,
            feedback: feedback,
            api: api,
            matchId: matchId,
            playerLabel: playerLabel
        ))
    }

    var body: some View {
        VStack(spacing: 0) {
            messagesList
            suggestedPromptsBar
            inputBar
        }
        .background(
            LinearGradient(
                colors: [
                    sportType.color.opacity(0.06),
                    Color(.systemGroupedBackground)
                ],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()
        )
        .navigationTitle("AI Coach")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .principal) {
                HStack(spacing: 8) {
                    CoachAvatar(accent: sportType.color, size: 26)
                    Text("AI Coach")
                        .font(.headline)
                }
            }
        }
    }

    private var messagesList: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(spacing: 14) {
                    ForEach(viewModel.messages) { message in
                        MessageBubble(message: message, accent: sportType.color)
                            .id(message.id)
                            .transition(.asymmetric(
                                insertion: .move(edge: message.role == .user ? .trailing : .leading)
                                    .combined(with: .opacity),
                                removal: .opacity
                            ))
                    }

                    if viewModel.isThinking {
                        HStack(alignment: .bottom, spacing: 8) {
                            CoachAvatar(accent: sportType.color, size: 30)
                            TypingIndicator(accent: sportType.color)
                            Spacer(minLength: 40)
                        }
                        .id("typing")
                    }
                }
                .padding(.horizontal)
                .padding(.vertical, 16)
            }
            .scrollDismissesKeyboard(.interactively)
            .onChange(of: viewModel.messages.count) { _, _ in
                scrollToBottom(proxy)
            }
            .onChange(of: viewModel.isThinking) { _, thinking in
                if thinking { withAnimation(.spring(response: 0.35)) { proxy.scrollTo("typing", anchor: .bottom) } }
            }
        }
    }

    private func scrollToBottom(_ proxy: ScrollViewProxy) {
        guard let last = viewModel.messages.last else { return }
        withAnimation(.spring(response: 0.4, dampingFraction: 0.85)) {
            proxy.scrollTo(last.id, anchor: .bottom)
        }
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
                            .fontWeight(.semibold)
                            .padding(.horizontal, 14)
                            .padding(.vertical, 9)
                            .background(
                                Capsule()
                                    .fill(sportType.color.opacity(0.12))
                            )
                            .overlay(
                                Capsule()
                                    .strokeBorder(sportType.color.opacity(0.25), lineWidth: 1)
                            )
                            .foregroundStyle(sportType.color)
                    }
                    .disabled(viewModel.isThinking)
                }
            }
            .padding(.horizontal)
            .padding(.vertical, 8)
        }
    }

    private var inputBar: some View {
        HStack(spacing: 10) {
            TextField("Ask your coach…", text: $viewModel.inputText, axis: .vertical)
                .textFieldStyle(.plain)
                .padding(.horizontal, 16)
                .padding(.vertical, 11)
                .background(
                    Capsule(style: .continuous)
                        .fill(Color(.systemBackground))
                )
                .overlay(
                    Capsule(style: .continuous)
                        .strokeBorder(Color(.separator).opacity(0.5), lineWidth: 1)
                )
                .lineLimit(1...4)
                .onSubmit { if viewModel.canSend { viewModel.send() } }

            Button {
                viewModel.send()
            } label: {
                Image(systemName: "arrow.up")
                    .font(.system(size: 17, weight: .bold))
                    .foregroundStyle(.white)
                    .frame(width: 40, height: 40)
                    .background(
                        Circle().fill(
                            viewModel.canSend
                            ? AnyShapeStyle(sportType.color.gradient)
                            : AnyShapeStyle(Color.gray.opacity(0.35))
                        )
                    )
                    .shadow(color: viewModel.canSend ? sportType.color.opacity(0.35) : .clear, radius: 6, y: 3)
            }
            .disabled(!viewModel.canSend)
            .animation(.easeInOut(duration: 0.15), value: viewModel.canSend)
        }
        .padding(.horizontal)
        .padding(.vertical, 10)
        .background(.ultraThinMaterial)
    }
}

// MARK: - Coach Avatar

private struct CoachAvatar: View {
    let accent: Color
    var size: CGFloat = 30

    var body: some View {
        Image(systemName: "figure.tennis")
            .font(.system(size: size * 0.5, weight: .bold))
            .foregroundStyle(.white)
            .frame(width: size, height: size)
            .background(Circle().fill(accent.gradient))
            .shadow(color: accent.opacity(0.3), radius: 3, y: 1)
    }
}

// MARK: - Message Bubble

private struct MessageBubble: View {
    let message: CoachChatMessage
    let accent: Color

    private var isUser: Bool { message.role == .user }

    var body: some View {
        HStack(alignment: .bottom, spacing: 8) {
            if isUser {
                Spacer(minLength: 44)
            } else {
                CoachAvatar(accent: accent, size: 30)
            }

            VStack(alignment: isUser ? .trailing : .leading, spacing: 4) {
                if !isUser {
                    Text("Coach")
                        .font(.caption2)
                        .fontWeight(.semibold)
                        .foregroundStyle(accent)
                }

                MarkdownText(message.text)
                    .font(.subheadline)
                    .foregroundStyle(isUser ? .white : .primary)
                    .padding(.horizontal, 15)
                    .padding(.vertical, 11)
                    .background(bubbleBackground)
                    .clipShape(BubbleShape(isUser: isUser))
                    .shadow(color: .black.opacity(isUser ? 0.12 : 0.06), radius: 5, y: 2)
            }

            if !isUser { Spacer(minLength: 44) }
        }
    }

    private var bubbleBackground: AnyShapeStyle {
        if isUser {
            AnyShapeStyle(accent.gradient)
        } else {
            AnyShapeStyle(Color(.systemBackground))
        }
    }
}

/// Chat bubble with a subtle "tail" corner on the sender's side.
private struct BubbleShape: Shape {
    let isUser: Bool
    func path(in rect: CGRect) -> Path {
        let radii = RectangleCornerRadii(
            topLeading: 18,
            bottomLeading: isUser ? 18 : 5,
            bottomTrailing: isUser ? 5 : 18,
            topTrailing: 18
        )
        return Path(roundedRect: rect, cornerRadii: radii, style: .continuous)
    }
}

// MARK: - Markdown Rendering

/// Renders lightweight Markdown (bold, italic, bullet lists, paragraph breaks)
/// line-by-line, since SwiftUI's inline markdown alone collapses newlines/lists.
private struct MarkdownText: View {
    let raw: String

    init(_ raw: String) { self.raw = raw }

    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            ForEach(Array(lines.enumerated()), id: \.offset) { _, line in
                switch line {
                case .blank:
                    Color.clear.frame(height: 2)
                case .bullet(let text):
                    HStack(alignment: .firstTextBaseline, spacing: 7) {
                        Text("•").fontWeight(.bold)
                        inlineText(text)
                    }
                case .paragraph(let text):
                    inlineText(text)
                }
            }
        }
        .fixedSize(horizontal: false, vertical: true)
    }

    private func inlineText(_ text: String) -> Text {
        if let attributed = try? AttributedString(
            markdown: text,
            options: .init(interpretedSyntax: .inlineOnlyPreservingWhitespace)
        ) {
            return Text(attributed)
        }
        return Text(text)
    }

    private enum Line {
        case paragraph(String)
        case bullet(String)
        case blank
    }

    private var lines: [Line] {
        raw.components(separatedBy: "\n").map { rawLine in
            let trimmed = rawLine.trimmingCharacters(in: .whitespaces)
            if trimmed.isEmpty { return .blank }
            // Common bullet markers the model may emit.
            for marker in ["- ", "* ", "• "] where trimmed.hasPrefix(marker) {
                return .bullet(String(trimmed.dropFirst(marker.count)))
            }
            return .paragraph(trimmed)
        }
    }
}

// MARK: - Typing Indicator

private struct TypingIndicator: View {
    let accent: Color
    @State private var phase = 0.0

    var body: some View {
        HStack(spacing: 5) {
            ForEach(0..<3) { i in
                Circle()
                    .fill(accent.opacity(0.7))
                    .frame(width: 7, height: 7)
                    .scaleEffect(scale(for: i))
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 13)
        .background(Color(.systemBackground))
        .clipShape(BubbleShape(isUser: false))
        .shadow(color: .black.opacity(0.06), radius: 5, y: 2)
        .onAppear {
            withAnimation(.easeInOut(duration: 0.6).repeatForever(autoreverses: false)) {
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
