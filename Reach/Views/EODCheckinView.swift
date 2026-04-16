//
//  EODCheckin.swift
//  Reach
//
//  Created by Shahd Alghurbani on 3/17/26.
//

import SwiftUI

struct EODCheckinView: View {
    //removed AppState + onAccountTap using global state instead
    //from Audiomanager.swift
    @State private var audioManager = AudioManager()
    
    var body: some View {
        VStack(spacing: 0) {
            //HeaderView(isDemoMode: $isDemoMode, showSignIn: $showSignIn)
            HeaderView()
            VStack(spacing: 0) {
                
                // Check if we should show the review screen or the mic screen
                if audioManager.showReview {
                    reviewSummarySection
                } else {
                    recordingSection
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            .background(Color(red: 0.93, green: 0.93, blue: 0.93))
            
            BottomNavView()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .background(Color.black)
        .ignoresSafeArea(edges: .bottom)
    }
    
    var recordingSection: some View {
        VStack(spacing: 0) {
            Text("End of Day \nCheck in")
                .font(.system(size: 42, weight: .regular))
                .foregroundColor(.black)
                .multilineTextAlignment(.center)
                .padding(.top, 40)

            VStack(spacing: 11) {
                Text("Heading to Bed?")
                    .font(.system(size: 24, weight: .semibold))

                Text("Reflect on your day. Tell me about your goals and how you met them. Your words become insights to better your experience.")
                    .font(.system(size: 14))
                    .multilineTextAlignment(.center)
                    .foregroundColor(.gray)
                    .lineSpacing(4)
            }
            .padding(32)
            .background(Color(red: 0.95, green: 0.92, blue: 0.96))
            .cornerRadius(30)
            .padding(.horizontal, 30)
            .padding(.top, 30)

            // button connection to audio manager, starts recording when pressed
            Button(action: { audioManager.toggleRecording(at: .endOfDay) }) {
                Image(systemName: "mic.fill")
                    .font(.system(size: 35))
                    .foregroundColor(.white)
                    .frame(width: 80, height: 80)
                
                    // color changes based on audio manager state
                    .background(audioManager.isRecording ? .red : Color(red: 0.45, green: 0.35, blue: 0.65))
                    .clipShape(Circle())
                    .shadow(color: .black.opacity(0.1), radius: 4, x: 0, y: 4)
            }
            .padding(.top, 50)
            .buttonStyle(MicButtonStyle())

            // while waiting for LLM response, shows the user "analyzing your day"
            if audioManager.isUploading {
                ProgressView("Analyzing your day...")
                    .padding(.top, 20)
                
                //if user is still recording, displays this
            } else {
                Text(audioManager.isRecording ? "Listening..." : "Press to begin to speak")
                    .font(.system(size: 20, weight: .regular))
                    .foregroundColor(audioManager.isRecording ? .red : .black)
                    .padding(.top, 24)
            }
        }
    }
    
    var reviewSummarySection: some View {
        VStack(spacing: 20) {
            Text("Your Summary")
                .font(.system(size: 32, weight: .bold))
                .padding(.top, 40)
            
            ScrollView {
                Text(audioManager.summary)
                    .padding()
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(Color.white)
                    .cornerRadius(15)
                    .padding(.horizontal, 30)
            }
            
            HStack(spacing: 20) {
                Button("Re-record") {
                    audioManager.showReview = false
                }
                .padding()
                .frame(maxWidth: .infinity)
                .background(Color.gray.opacity(0.2))
                .cornerRadius(15)
                
                Button("Looks good") {
                    audioManager.saveConversation()
                }
                .padding()
                .frame(maxWidth: .infinity)
                .background(Color(red: 0.45, green: 0.35, blue: 0.65))
                .foregroundColor(.white)
                .cornerRadius(15)
            }
            .padding(.horizontal, 30)
            .padding(.bottom, 40)
        }
    }
}

struct MicButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.92 : 1.0)
            .opacity(configuration.isPressed ? 0.9 : 1.0)
            .animation(.spring(response: 0.3, dampingFraction: 0.6), value: configuration.isPressed)
    }
}

#Preview {
    EODCheckinView()
}
