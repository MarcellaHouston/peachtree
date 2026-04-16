//
//  WeeklyRecapView.swift
//  Reach
//
//  Created by Ismael Medina on 3/25/26.
//
import SwiftUI

struct WeeklyRecapView: View {
    /*
    let weekText = "Feb 10 - Feb 16, 2026"
    let summaryText = "You removed the gym goal, paused journaling, and continued working on your remaining goals this week. Focus next on meal prep, studying, and keeping your daily routines consistent."
    let suggestionText = "Focus on consistency by reducing daily job applications and structuring study into focused sessions. Maintain journaling and weekly meal prep for steady progress."
    let completedTaskCount = 10
    let totalTaskCount = 12
    @State var showingPopup: Bool = false
     */
    let weekText = "Feb 10 - Feb 16, 2026"
    @State private var summaryText = "Loading weekly summary..."
    @State private var suggestionTitle = "Loading title..."
    @State private var suggestionText = "Loading suggestions..."
    //Change Tasks Completed to Reflect Backend Tasks Completed Info
    @State private var completedTaskCount = 0
    @State private var totalTaskCount = 0
    @State private var showingPopup = false
    @State private var isLoadingRecap = false
    
    var body: some View {
        VStack(spacing: 0) {
            HeaderView()

            VStack {
                // Header
                Text("Weekly Recap")
                    .font(.system(size: 42, weight: .regular))
                    .foregroundColor(.black)
                    .frame(maxWidth: .infinity)
                    .multilineTextAlignment(.center)
                    .padding(.top, 48)
                    .padding(.bottom, 3)

                // Black box with week dates
                Text(weekText)
                    .font(.system(size: 15))
                    .frame(minWidth: 173, minHeight: 46)
                    .foregroundColor(.white)
                    .background(.black)
                    .cornerRadius(10)
                
                // Weekly Summary section
                VStack {
                    Text("Weekly Summary").font(.system(size: 28)).BigHeader().padding(.top, 5).padding(.bottom, 5)
                    Text(summaryText).font(.system(size:13)).padding(.horizontal, 5).padding(.bottom, 5)
                }
                .frame(width: 326, height: 148)
                .background(.white)
                .cornerRadius(20)

                // Progress Bar
                TaskProgressBar(completedTaskCount: completedTaskCount, totalTaskCount: totalTaskCount)
                
                // AI Suggestions
                VStack {
                    HStack {
                        Circle()
                            .frame(width: 40)
                            .foregroundColor(Color(red: 0.52, green: 0.21, blue: 0.95))
                            .overlay(Text("+").foregroundColor(.white))
                            .padding(.horizontal, 10)
                        VStack {
                            Text("AI Suggestions").SmallHeader()
                            Text("Next steps to stay on track").font(.system(size:13))
                        }.frame(alignment: .leading)
                        Spacer()
                        Image(systemName: "sparkles")
                            .font(.system(size: 30))
                            .foregroundColor(.purple)
                            .padding(.horizontal, 10)
                    }
                    .padding(.vertical, 2)
                    
                    //TODO: DEBUGGING NOTES 4/16/26 4AM
                    //different words for this "This is the theme of AI change",
                    //"Overarching goal of LLM" something similar
                    //AI suggestion should be some type of check mark where the user
                    //selects specific checkmark items to backend and is updated afterwards
                    Text(suggestionTitle).SmallHeader()
                    Text(suggestionText).font(.system(size:13)).padding(.horizontal, 5).padding(.bottom, 5)
                }
                .frame(width: 360, height: 141)
                .background(Color(red: 254, green: 247, blue: 255))
                .cornerRadius(20)
                .onTapGesture {
                    showingPopup = true
                }
                
            } // End of content
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            .background(Color(red: 0.93, green: 0.93, blue: 0.93))
            BottomNavView()
        }
        .background(Color.black)
        .ignoresSafeArea(edges: .bottom)
        .overlay{
            if showingPopup {
                Color.black.opacity(0.35)
                    .ignoresSafeArea()
                GoalSuggestionsPopup(isShowing: $showingPopup)
            }
        }
        
        // weekly recap auto fetch start
        .task {
            print("=== WEEKLY RECAP CALL START ===")
            
            isLoadingRecap = true

            await ApiCall.shared.refreshGoals()

            if let recap = await ApiCall.shared.fetchWeeklyRecap() {
                print("weekly summary:", recap.weeklySummary)
                print("changes title:", recap.changesTitle)
                print("changes summary:", recap.changesSummary)
                print("weekly suggestions:", recap.suggestions)
                print("weekly stats completed:", recap.completed)
                print("weekly stats total:", recap.total)

                summaryText = recap.weeklySummary
                suggestionTitle = recap.changesTitle
                suggestionText = recap.changesSummary
                completedTaskCount = recap.completed
                totalTaskCount = recap.total
            } else {
                print("weekly recap returned no recommendations")

                summaryText = "No recommendations this week"
                suggestionTitle = "No changes needed"
                suggestionText = "You're all caught up"
                completedTaskCount = 0
                totalTaskCount = 0
            }

            isLoadingRecap = false

            print("=== WEEKLY RECAP CALL END ===")
        }
        // weekly recap auto fetch end
    }
}

#Preview {
    WeeklyRecapView()
}
