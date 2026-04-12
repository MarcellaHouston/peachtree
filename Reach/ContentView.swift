//
//  ContentView.swift
//  Reach
//
//  Created by Ismael Medina on 2/24/26.
//
import SwiftUI

//display TodayTasksView
struct ContentView: View {
    /*
    @State private var selectedTab: AppTab = .todayTasks
    
    //this controls which screen shows first
    @State private var showSignIn = true
    
    //this tracks whether the user entered through demo mode
    @State private var isDemoMode = false
    @State private var showDemoPopup = false
    */
    //This is used instead of the previous @State by using struct definition in AppState.swift
    @State private var appState = AppState()
    @State private var showSignOutPopup = false
    
    var body: some View {
        Group {
            if appState.showSignIn {
                if appState.authScreen == .signIn
                {
                    SignInView(appState: $appState)
                } else{
                    SignUpView(appState: $appState)
                }
            } else {
                switch appState.selectedTab {
                case .todayTasks:
                    TodayTasksView(appState: $appState, onAccountTap: { showSignOutPopup = true })
                case .goals:
                    GoalsView(appState: $appState, onAccountTap: {showSignOutPopup = true})
                case .weeklyRecap:
                    WeeklyRecapView(appState: $appState, onAccountTap: { showSignOutPopup = true})
                case .endOfDay:
                    EODCheckinView(appState: $appState, onAccountTap: {showSignOutPopup = true})
                }
            }
        }
        .overlay {
            if appState.showDemoPopup {
                Color.black.opacity(0.35)
                    .ignoresSafeArea()

                VStack {
                    Spacer()
                    DemoConfirmPopup(appState: $appState)
                    Spacer()
                }
            }
            
            //Sign Out Popup
            else if showSignOutPopup {
                Color.black.opacity(0.35)
                    .ignoresSafeArea()

                VStack {
                    Spacer()
                    SignOutPopup(appState: $appState, isShowing: $showSignOutPopup)
                    Spacer()
                }
            }
        }
    }
}

#Preview {
    ContentView()
}
