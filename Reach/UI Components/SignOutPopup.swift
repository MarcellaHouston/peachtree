//
//  SignOutPopup.swift
//  Reach
//
//  Created by Ismael Medina on 4/10/26.
//

import SwiftUI

struct SignOutPopup: View {
    private let appState = AppState.shared
    private let accentPurple = Color(red: 112 / 255, green: 88 / 255, blue: 184 / 255)

    var body: some View {
        VStack(spacing: 0) {
            VStack(spacing: 0) {
                Circle()
                    .fill(Color(red: 0.88, green: 0.83, blue: 0.97))
                    .frame(width: 54, height: 54)
                    .overlay {
                        Image(systemName: "person.crop.circle")
                            .font(.system(size: 28, weight: .regular))
                            .foregroundColor(Color(red: 0.34, green: 0.26, blue: 0.64))
                    }
                    .padding(.top, 22)

                Text(UserCreds.shared.getStringId() ?? "Account name failed to load")
                    .font(.system(size: 20, weight: .semibold))
                    .foregroundColor(.black)
                    .padding(.top, 12)

                Text("You are currently signed in.")
                    .font(.system(size: 13, weight: .regular))
                    .foregroundColor(.black.opacity(0.7))
                    .padding(.top, 10)

                HStack(spacing: 22) {
                    Button("Cancel") {
                        appState.showSignOutPopup = false
                    }
                    .font(.system(size: 14, weight: .regular))
                    .foregroundColor(.black.opacity(0.8))

                    Button("Sign Out") {
                        UserCreds.shared.delete()
                        appState.showSignOutPopup = false
                        appState.isDemoMode = false
                        appState.showDemoPopup = false
                        appState.selectedTab = .todayTasks
                        appState.showSignIn = true
                    }
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(accentPurple)
                }
                .padding(.top, 20)
                .padding(.bottom, 22)
            }
            .padding(.horizontal, 20)
        }
        .frame(width: 290)
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: 18))
        .shadow(color: Color.black.opacity(0.2), radius: 10, x: 0, y: 4)
    }
}

#Preview {
    SignOutPopup()
}
