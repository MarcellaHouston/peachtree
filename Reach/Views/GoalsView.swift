//
//  GoalsView.swift
//  Reach
//
//  Created by Ismael Medina on 3/25/26.
//

import SwiftUI

//to handle one view for both editing goals and goal guidance screen
enum GoalsListMode {
    case edit  // tapping a row opens EditGoalView
    case guidance  // tapping a row opens a guidance popup (placeholder for now)
}

//this is the main goals screen view
//it handles displaying goals, opening edit/new goal popups, and switching tabs
struct GoalsView: View {
    //binding to control which tab is currently selected in the app
    @Binding var selectedTab: AppTab
    //this keeps track of which goal is currently selected when user taps one
    @State private var selectedGoal: GoalItem? = nil

    //controls whether the edit goal popup is visible
    @State private var showEditGoal = false

    //controls whether the new goal popup is visible
    @State private var showNewGoal = false

    //controls whether the guidance screen is open
    //will eventually connect to goal-specific goal guidance view
    @State private var showGuidance = false

    @State private var currentMode: GoalsListMode = .edit

    var body: some View {
        //outer container for header, content, nav
        VStack(spacing: 0) {
            HeaderView()
            //main content
            VStack(spacing: 0) {
                //Goals Formatting and Text title
                Text("Goals")
                    .font(.system(size: 42, weight: .regular))
                    .foregroundColor(.black)
                    .frame(maxWidth: .infinity)
                    .multilineTextAlignment(.center)
                    .padding(.top, 48)
                    .padding(.bottom, 34)
                    .overlay(alignment: .topTrailing) {
                        //Moon Icon
                        Button {
                            selectedTab = .endOfDay
                        } label: {
                            Image(systemName: "moon.circle.fill")
                                .font(.system(size: 50, weight: .regular))
                                .foregroundColor(
                                    Color(red: 0.34, green: 0.26, blue: 0.64)
                                )
                        }
                        .padding(.top, 26)
                        .padding(.trailing, 28)
                    }
                //Enable scrolling, showIndicators indicates the scroll bar thingy
                ScrollView(showsIndicators: true) {
                    VStack(spacing: 22) {
                        //loops through each goal and creates a row
                        //when tapped, it opens the edit goal popup or if gg mode, opens the gg menu for *that* goal
                        ForEach(ApiCall.shared.goals, id: \.id) { goal in
                            GoalRow(
                                goal: goal,
                                iconSystemName: currentMode == .edit
                                    ? "pencil" : "sparkles"
                            ) {
                                selectedGoal = goal
                                switch currentMode {
                                case .edit:
                                    showEditGoal = true
                                case .guidance:
                                    showGuidance = true
                                }
                            }
                        }
                    }
                    .padding(.horizontal, 28)
                    .padding(.bottom, 20)
                }
                //pushes plus button to the bottom right and gg button to the bottom left
                Spacer(minLength: 0)
                //plus button code
                HStack {

                    //press to enter guidance mode, press again to go back to edit mode
                    Button {
                       if(currentMode == .guidance)
                        {
                            currentMode = .edit
                        }
                        
                        else {
                            currentMode = .guidance
                            
                        }
                    } label: {
                        Circle()
                            .fill(Color(red: 0.50, green: 0.37, blue: 0.77))
                            .frame(width: 58, height: 58)

                            .overlay {
                                if(currentMode == .guidance)
                                {
                                    Image(systemName: "arrow.left")
                                        .font(.system(size: 25, weight: .regular))
                                        .foregroundColor(.white)
                                }
                                
                                else
                                {
                                    //public library for ai button thing
                                    Image(systemName: "sparkles")
                                        .font(.system(size: 25, weight: .regular))
                                        .foregroundColor(.white)
                                }
                            }

                    }

                    Spacer()
                    if currentMode == .edit {

                        Button {
                            showNewGoal = true
                        } label: {
                            Circle()
                                .fill(Color(red: 0.50, green: 0.37, blue: 0.77))
                                .frame(width: 58, height: 58)
                                .overlay {
                                    //public library for plus
                                    Image(systemName: "plus")
                                        .font(
                                            .system(size: 25, weight: .regular)
                                        )
                                        .foregroundColor(.white)
                                }
                        }
                        .buttonStyle(.plain)
                    }
                    
                    else
                    {
                        VStack
                        {
                            Text("Thinking about adjusting a goal? Tap one to receive goal guidance!")
                        }
                    }

                }
                .padding(.horizontal, 34)
                .padding(.bottom, 22)
            }

            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            .background(Color(red: 0.93, green: 0.93, blue: 0.93))
            //nav bar integration
            BottomNavView(selectedTab: $selectedTab)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .background(Color.black)
        //extends UI to edges
        .ignoresSafeArea(edges: .bottom)
        //overlay used for popups, dim background
        .overlay {
            if showEditGoal, let selectedGoal, currentMode == .edit {
                Color.black.opacity(0.35)
                    .ignoresSafeArea()

                EditGoalView(goal: selectedGoal, isShowing: $showEditGoal)
            } else if showNewGoal {
                Color.black.opacity(0.35)
                    .ignoresSafeArea()

                NewGoalView(isShowing: $showNewGoal)
            }
        }
        //runs when the view appears
        //tries to fetch goals from backend first
        //if backend is empty, fallback data is used instead
        .task {
            await ApiCall.shared.refreshGoals()
        }
    }
}

//builds each individual goal row
//entire row is clickable and opens the edit goal popup
private struct GoalRow: View {
    let goal: GoalItem
    let iconSystemName: String
    let onTap: () -> Void

    var body: some View {
        //horizontal row display of goal item and pencil as well as some padding
        Button(action: onTap) {
            HStack {

                // left spacer to balance the pencil width
                Spacer()
                    .frame(width: 24)
                //title of each goal
                Text(goal.title)
                    .font(.system(size: 15, weight: .regular))
                    .foregroundColor(.black)
                    .lineLimit(1)
                    .frame(maxWidth: .infinity, alignment: .center)

                //iconSystem variable to switch between the pencil and sparkles icon depending on the mode (edit vs guidance)
                Image(systemName: iconSystemName)
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.white)
                    .frame(width: 24)
            }

            .padding(.horizontal, 12)
            .frame(height: 46)
            .frame(maxWidth: .infinity)
            // make goal gray if it's paused
            .background(
                goal.isPaused
                    ? Color(red: 0.63, green: 0.63, blue: 0.63)
                    : Color(red: 0.77, green: 0.69, blue: 0.94)
            )
            .clipShape(RoundedRectangle(cornerRadius: 16))
            .frame(height: 46)

            .frame(maxWidth: .infinity)

            .clipShape(RoundedRectangle(cornerRadius: 16))
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    GoalsView(selectedTab: .constant(.goals))
}
