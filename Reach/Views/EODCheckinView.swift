//
//  EODCheckin.swift
//  Reach
//
//  Created by Shahd Alghurbani on 3/17/26.
//

import SwiftUI

struct EODCheckinView: View {
    @Binding var selectedTab: AppTab
    @State private var isRecording = false
    
    
    var body: some View {
        VStack(spacing: 0) {
            //header at the top of the screen containing the status bar and profile section
            HeaderView()

            VStack(spacing: 0) {
                Text("End of Day \nCheck in")
                    .font(.system(size: 42, weight: .regular))
                    .foregroundColor(.black)
                    .multilineTextAlignment(.center)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: .infinity)
                    .padding(.top, 40)

                //Info Card

                VStack(spacing: 11) {
                    Text("Heading to Bed?")
                        .font(.system(size: 24, weight: .semibold))

                    Text(
                        "Reflect on your day. Tell me about your goals and how you met them. Your words become insights to better your experience."
                    )
                    .font(.system(size: 14))
                    .multilineTextAlignment(.center)
                    .foregroundColor(.gray)
                    .lineSpacing(4)
                    .fixedSize(horizontal: false, vertical: true)
                }

                .padding(32)
                .background(Color(red: 0.95, green: 0.92, blue: 0.96))  // soft lavender color from Figma
                .cornerRadius(30)
                .padding(.horizontal, 30)
                .padding(.top, 30)

                Spacer()

                //mic button stuff

                Button(action: { isRecording.toggle() }) {
                    Image(systemName: "mic.fill")
                        .font(.system(size: 35))
                        .foregroundColor(.white)
                        .frame(width: 80, height: 80)  // Size of the circle
                        .background(Color(red: 0.45, green: 0.35, blue: 0.65))  // The circle color
                        .clipShape(Circle())  // Makes the bg a circle under mic
                        .shadow(
                            color: .black.opacity(0.1),
                            radius: 4,
                            x: 0,
                            y: 4
                        )
                }

                .buttonStyle(MicButtonStyle())

                Text(isRecording ? "Listening..." : "Press to begin to speak")
                    .font(.system(size: 20, weight: .regular))
                    .foregroundColor(isRecording ? .red : .black)
                    .padding(.top, 24)
                Spacer()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(Color(red: 0.93, green: 0.93, blue: 0.93))
            }
            //bottom navigation bar for switching between tabs
            BottomNavView(selectedTab: $selectedTab)

        }

        .background(Color(red: 0.93, green: 0.93, blue: 0.93).ignoresSafeArea())
    }
}

struct MicButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.92 : 1.0)
            .opacity(configuration.isPressed ? 0.9 : 1.0)
    }
}
