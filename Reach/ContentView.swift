//
//  ContentView.swift
//  Reach
//
//  Created by Ismael Medina on 2/24/26.
//
import SwiftUI

// auth screen enum moved here since it's only used for switching auth views
enum AuthScreen {
    case signIn
    case signUp
}
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
    //moved auth screen state out of AppState into contentview
    @State private var authScreen: AuthScreen = .signIn
    private let appState = AppState.shared
    
    var body: some View {
        Group {
            if appState.showSignIn && UserCreds.shared.getToken() == nil {
                if authScreen == .signIn
                {
                    //pass authScreen binding down to child views
                    SignInView(authScreen: $authScreen)
                } else{
                    SignUpView(authScreen: $authScreen)
                }
            } else {
                switch appState.selectedTab {
                case .todayTasks:
                    TodayTasksView()
                case .goals:
                    GoalsView()
                case .weeklyRecap:
                    WeeklyRecapView()
                case .endOfDay:
                    EODCheckinView()
                }
            }
        }
        .overlay {
            if appState.showDemoPopup {
                Color.black.opacity(0.35)
                    .ignoresSafeArea()

                VStack {
                    Spacer()
                    DemoConfirmPopup()
                    Spacer()
                }
            }
            
            //Sign Out Popup
            else if appState.showSignOutPopup {
                Color.black.opacity(0.35)
                    .ignoresSafeArea()

                VStack {
                    Spacer()
                    SignOutPopup()
                    Spacer()
                }
            }
        }
    }
}

#Preview {
    ContentView()
}
