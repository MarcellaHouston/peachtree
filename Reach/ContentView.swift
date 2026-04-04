//
//  ContentView.swift
//  Reach
//
//  Created by Ismael Medina on 2/24/26.
//
import SwiftUI

//display TodayTasksView
struct ContentView: View {
    @State private var selectedTab: AppTab = .todayTasks
    
    //this controls which screen shows first
    @State private var showSignIn = true
    
    //this tracks whether the user entered through demo mode
    @State private var isDemoMode = false
    @State private var showDemoPopup = false
    
    var body: some View {
        Group {
            if showSignIn {
                SignInView(showSignIn: $showSignIn, isDemoMode: $isDemoMode, showDemoPopup: $showDemoPopup, selectedTab: $selectedTab)
            } else {
                switch selectedTab {
                case .todayTasks:
                    TodayTasksView(selectedTab: $selectedTab, isDemoMode: $isDemoMode, showSignIn: $showSignIn, showDemoPopup: $showDemoPopup)
                case .goals:
                    GoalsView(selectedTab: $selectedTab, isDemoMode: $isDemoMode, showSignIn: $showSignIn, showDemoPopup: $showDemoPopup)
                case .weeklyRecap:
                    WeeklyRecapView(selectedTab: $selectedTab, isDemoMode: $isDemoMode, showSignIn: $showSignIn, showDemoPopup: $showDemoPopup)
                case .endOfDay:
                    EODCheckinView(selectedTab: $selectedTab, isDemoMode: $isDemoMode, showSignIn: $showSignIn, showDemoPopup: $showDemoPopup)
                }
            }
        }
        .overlay {
            if showDemoPopup {
                Color.black.opacity(0.35)
                    .ignoresSafeArea()

                VStack {
                    Spacer()
                    DemoConfirmPopup(showDemoPopup: $showDemoPopup, showSignIn: $showSignIn, isDemoMode: $isDemoMode, selectedTab: $selectedTab)
                    Spacer()
                }
            }
        }
    }
}

#Preview {
    ContentView()
}
