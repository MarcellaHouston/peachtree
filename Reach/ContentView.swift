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
    
    var body: some View {
        switch selectedTab {
        case .todayTasks:
            TodayTasksView(selectedTab: $selectedTab)
        case .goals:
            GoalsView(selectedTab: $selectedTab)
        case .weeklyRecap:
            WeeklyRecapView(selectedTab: $selectedTab)
        case .endOfDay:
            EODCheckinView(selectedTab: $selectedTab)
        }
    }
}

#Preview {
    ContentView()
}
