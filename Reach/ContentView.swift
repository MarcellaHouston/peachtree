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
                    //TodayTasksView(selectedTab: $selectedTab, isDemoMode: $isDemoMode, showSignIn: $showSignIn, showDemoPopup: $showDemoPopup)
                case .goals:
                    GoalsView(appState: $appState, onAccountTap: {showSignOutPopup = true})
                    //GoalsView(selectedTab: $selectedTab, isDemoMode: $isDemoMode, showSignIn: $showSignIn, showDemoPopup: $showDemoPopup)
                case .weeklyRecap:
                    //WeeklyRecapView(appState: $appState, onAccountTap: {showSignOutPopup = true})
                    WeeklyRecapView(appState: $appState)
                    //WeeklyRecapView(selectedTab: $selectedTab, isDemoMode: $isDemoMode, showSignIn: $showSignIn, showDemoPopup: $showDemoPopup)
                case .endOfDay:
                    EODCheckinView(appState: $appState, onAccountTap: {showSignOutPopup = true})
                    //EODCheckinView(selectedTab: $selectedTab, isDemoMode: $isDemoMode, showSignIn: $showSignIn, showDemoPopup: $showDemoPopup)
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
                    //DemoConfirmPopup(showDemoPopup: $showDemoPopup, showSignIn: $showSignIn, isDemoMode: $isDemoMode, selectedTab: $selectedTab)
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
