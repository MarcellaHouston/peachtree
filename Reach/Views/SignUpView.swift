//
//  SignUpView.swift
//  Reach
//
//  Created by Ismael Medina on 4/10/26.
//

import SwiftUI

struct SignUpView: View {
    // receive authScreen from ContentView (moved out of AppState)
    @Binding var authScreen: AuthScreen
    
    private let appState = AppState.shared
    //This is temporary will change after receiving backend portion
    //Do not worry about this
    @State private var username = ""
    @State private var password = ""

    private let headerPurple = Color(red: 186 / 255, green: 171 / 255, blue: 228 / 255)
    private let waveFillPurple = Color(red: 181 / 255, green: 167 / 255, blue: 225 / 255)
    private let waveLinePurple = Color(red: 137 / 255, green: 109 / 255, blue: 199 / 255)
    private let accentPurple = Color(red: 112 / 255, green: 88 / 255, blue: 184 / 255)
    private let lineGray = Color.black.opacity(0.42)
    private let placeholderGray = Color(red: 187 / 255, green: 187 / 255, blue: 187 / 255)

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {

            //top section with filled tapered wave
            VStack(alignment: .leading, spacing: 0) {
                Rectangle()
                    .fill(headerPurple)
                    .frame(height: 305)
                    .overlay(alignment: .bottom) {
                        SignInWaveFill()
                            .fill(Color.white)
                            .frame(width: UIScreen.main.bounds.width + 36, height: 142)
                            .overlay(alignment: .top) {
                                SignInWaveLine()
                                    .stroke(waveLinePurple, lineWidth: 9)
                                    .frame(width: UIScreen.main.bounds.width + 36, height: 142)
                            }
                            .offset(x: 0, y: 2)
                    }
                    .clipped()

                VStack(alignment: .leading, spacing: 0) {
                    Text("Sign up")
                        .font(.system(size: 55, weight: .regular))
                        .foregroundColor(.black)
                        .padding(.top, -30)

                    Rectangle()
                        .fill(accentPurple)
                        .frame(width: 112, height: 4)
                        .padding(.top, 6)
                }
                .padding(.horizontal, 31)
            }

            VStack(alignment: .leading, spacing: 0) {
                Text("Username")
                    .font(.system(size: 14, weight: .regular))
                    .foregroundColor(.black)
                    .padding(.top, 34)

                TextField(
                    "",
                    text: $username,
                    prompt: Text("Sign Up Testing")
                        .foregroundColor(placeholderGray)
                )
                .font(.system(size: 14, weight: .regular))
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .padding(.top, 10)

                Rectangle()
                    .fill(lineGray)
                    .frame(height: 1)
                    .padding(.top, 8)

                Text("Password")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.black)
                    .padding(.top, 28)

                SecureField(
                    "",
                    text: $password,
                    prompt: Text("••••••••••••")
                        .foregroundColor(placeholderGray)
                )
                .font(.system(size: 14, weight: .regular))
                .padding(.top, 10)

                Rectangle()
                    .fill(lineGray)
                    .frame(height: 1)
                    .padding(.top, 8)
                
            
                .padding(.top, 12)
                Spacer()
                    .frame(height: 50)

                Button {
                    // switch back to sign in using local auth state
                    authScreen = .signIn
                    appState.showSignIn = false
                } label: {
                    Text("Create Account")
                        .font(.system(size: 17, weight: .semibold))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .frame(height: 42)
                        .background(accentPurple)
                        .clipShape(Capsule())
                }
                .frame(maxWidth: .infinity)
                .padding(.top, 14)
                
                HStack(spacing: 8) {
                    Text("Already have an account?")
                        .font(.system(size: 11, weight: .regular))
                        .foregroundColor(.black.opacity(0.78))

                    Button("Log In") {
                        // switch auth screen using local state instead of AppState
                        authScreen = .signIn
                    }
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(accentPurple)
                }
                .frame(maxWidth: .infinity)
                .padding(.top, 14)
                .padding(.bottom, 18)
            }
            .padding(.horizontal, 31)

            Spacer(minLength: 0)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .background(Color.white)
        .ignoresSafeArea()
    }
}

struct SignUpWaveFill: Shape {
    func path(in rect: CGRect) -> Path {
        var path = Path()

        let start = CGPoint(x: -24, y: rect.height * 0.72)
        let firstTop = CGPoint(x: rect.width * 0.33, y: rect.height * 0.24)
        let valley = CGPoint(x: rect.width * 0.70, y: rect.height * 0.78)
        let end = CGPoint(x: rect.width + 24, y: rect.height * 0.42)

        path.move(to: start)

        path.addCurve(
            to: firstTop,
            control1: CGPoint(x: rect.width * 0.10, y: rect.height * 0.46),
            control2: CGPoint(x: rect.width * 0.22, y: rect.height * 0.18)
        )

        path.addCurve(
            to: valley,
            control1: CGPoint(x: rect.width * 0.46, y: rect.height * 0.28),
            control2: CGPoint(x: rect.width * 0.56, y: rect.height * 0.92)
        )

        path.addCurve(
            to: end,
            control1: CGPoint(x: rect.width * 0.83, y: rect.height * 0.66),
            control2: CGPoint(x: rect.width * 0.94, y: rect.height * 0.50)
        )

        path.addLine(to: CGPoint(x: rect.width + 24, y: rect.height + 60))
        path.addLine(to: CGPoint(x: -24, y: rect.height + 60))
        path.closeSubpath()

        return path
    }
}

struct SignUpWaveLine: Shape {
    func path(in rect: CGRect) -> Path {
        var path = Path()

        let start = CGPoint(x: -24, y: rect.height * 0.72)
        let firstTop = CGPoint(x: rect.width * 0.33, y: rect.height * 0.24)
        let valley = CGPoint(x: rect.width * 0.70, y: rect.height * 0.78)
        let end = CGPoint(x: rect.width + 24, y: rect.height * 0.42)

        path.move(to: start)

        path.addCurve(
            to: firstTop,
            control1: CGPoint(x: rect.width * 0.10, y: rect.height * 0.46),
            control2: CGPoint(x: rect.width * 0.22, y: rect.height * 0.18)
        )

        path.addCurve(
            to: valley,
            control1: CGPoint(x: rect.width * 0.46, y: rect.height * 0.28),
            control2: CGPoint(x: rect.width * 0.56, y: rect.height * 0.92)
        )

        path.addCurve(
            to: end,
            control1: CGPoint(x: rect.width * 0.83, y: rect.height * 0.66),
            control2: CGPoint(x: rect.width * 0.94, y: rect.height * 0.50)
        )

        return path
    }
}

/*
 #Preview {
 SignInView(showSignIn: .constant(true), isDemoMode: .constant(false), showDemoPopup: .constant(false), selectedTab: .constant(.todayTasks))
 }
 */
#Preview {
    SignUpView(authScreen: .constant(.signIn))

}


