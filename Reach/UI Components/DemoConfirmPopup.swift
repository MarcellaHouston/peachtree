//
//  DemoConfirmPopup.swift
//  Reach
//
//  Created by Ismael Medina on 4/4/26.
//

import SwiftUI

//this view builds the demo confirmation popup shown on top of today's tasks
//it matches the figma design with centered layout and exact wording
struct DemoConfirmPopup: View {
    @Binding var appState: AppState

    private let accentPurple = Color(red: 112 / 255, green: 88 / 255, blue: 184 / 255)

    var body: some View {
        VStack(spacing: 0) {

            VStack(alignment: .leading, spacing: 0) {

                Text("You are in demo mode.")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(.black)
                    .padding(.top, 22)

                Text("Changes will not be saved")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(.black)
                    .padding(.top, 2)

                Text("Take a look around and try creating or updating goals to see how everything works. Your progress won’t be saved after you leave demo mode.")
                    .font(.system(size: 13, weight: .regular))
                    .foregroundColor(.black.opacity(0.7))
                    .padding(.top, 12)

                HStack(spacing: 20) {

                    Button("Continue Demo") {
                        appState.showDemoPopup = false
                    }
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(accentPurple)

                    Button("Leave Demo") {
                        appState.showDemoPopup = false
                        appState.isDemoMode = false
                        appState.showSignIn = true
                    }
                    .font(.system(size: 14, weight: .regular))
                    .foregroundColor(.black.opacity(0.8))
                }
                .padding(.top, 18)
                .frame(maxWidth: .infinity, alignment: .center)
                .padding(.bottom, 18)
            }
            .padding(.horizontal, 20)
        }
        //popup container
        .frame(width: 300)
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: 18))
        //shadow for depth like figma
        .shadow(color: Color.black.opacity(0.2), radius: 10, x: 0, y: 4)
    }
}
/*
 #Preview {
 DemoConfirmPopup(showDemoPopup: .constant(true), showSignIn: .constant(false), isDemoMode: .constant(true), selectedTab: .constant(.todayTasks))
 }
 */
#Preview {
    DemoConfirmPopup(appState: .constant(AppState(selectedTab: .todayTasks, showSignIn: false, isDemoMode: true, showDemoPopup: true)))
}
