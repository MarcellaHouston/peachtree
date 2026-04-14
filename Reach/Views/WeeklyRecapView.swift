//
//  WeeklyRecapView.swift
//  Reach
//
//  Created by Ismael Medina on 3/25/26.
//
import SwiftUI

struct WeeklyRecapView: View {
    //Removed since AppState is used
    //@Binding var selectedTab: AppTab
    let weekText = "Feb 10 - Feb 16, 2026"
    let summaryText = "You removed the gym goal, paused journaling, and continued working on your remaining goals this week. Focus next on meal prep, studying, and keeping your daily routines consistent."
    let suggestionText = "Focus on consistency by reducing daily job applications and structuring study into focused sessions. Maintain journaling and weekly meal prep for steady progress."
    let completedTaskCount = 10
    let totalTaskCount = 12
    @State var showingPopup: Bool = false
    
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
                    Text("Rebalance Daily Workload").SmallHeader()
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
    }
}

#Preview {
    WeeklyRecapView()
}
