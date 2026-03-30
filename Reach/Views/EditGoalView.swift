//
//  EditGoalView.swift
//  Reach
//
//  Created by Marcella Houston on 3/17/26.
//

import SwiftUI

struct EditGoalView: View {
    @State private var goal: GoalItem
    
    @State private var showingPausePopup = false
    @State private var showingDeletePopup = false
    
    // Store some @State variable wherever you call an EditGoalView
    // When you call init, set isShowingIn: $variable
    @Binding var isShowing: Bool
    
    init(goal goalIn: GoalItem, isShowing isShowingIn: Binding<Bool>){
        // This is a copy because GoalItem is a struct, not a class
        goal = goalIn
        _isShowing = isShowingIn
    }
    
    var body: some View {
        VStack(spacing: 0) {
            // Title and pause area
            HStack{
                TextField("Enter Goal Title", text: $goal.title)
                Button(goal.isPaused ? "Unpause" : "Pause") {
                    if goal.isPaused{
                        // Nothing
                    } else {
                        showingPausePopup = true
                    }
                }
                .buttonStyle(PurpleButtonStyle(active: goal.isPaused))

            }
            .padding(5)
            .frame(width: 360)
            
            // Header image
            Text("img")
                .frame(width: 360, height: 170)
                .background(Color.black)
            
            GoalOptions(goal: $goal, editMode: true)
            
            
            // Footer with delete and confirm buttons
            HStack {
                Button("Delete") {
                    showingDeletePopup = true
                }
                .buttonStyle(PurpleButtonStyle(active: false))
                Button("Cancel") {
                    isShowing = false
                }
                .buttonStyle(PurpleButtonStyle(active: false))
                Button("Save Changes") {
                    isShowing = false
                    Task {
                        await ApiCall.shared.updateGoal(goal: goal)
                    }
                }
                .buttonStyle(PurpleButtonStyle(active: true))
            }
            .frame(height: 50)
        }
        .background(.white)
        .frame(maxHeight: 570)
        .cornerRadius(15)
        
        // Confirmation popups are overlayed if their respective variables are on
        .overlay{
            if showingDeletePopup{
                ConfirmPopup(isShown: $showingDeletePopup, prompt: "Are you sure you want to delete this goal?", desc: "If you need to take a break, you can pause this goal instead. You can also use the AI Goal Guidance feature to help make the goal more manageable.", confirm: "Delete", effect: {
                    Task {
                        await ApiCall.shared.deleteGoal(goal: goal)
                    }
                    isShowing = false
                }
                )
            } else if showingPausePopup {
                ConfirmPopup(isShown: $showingPausePopup, prompt: "Need a break?", desc: "No worries—jump back in whenever you're ready. Want to keep going? Try AI Goal Guidance to make your goal more manageable.", confirm: "Pause Goal", effect: {
                    goal.isPaused = true
                    isShowing = false
                    Task {
                        await ApiCall.shared.snoozeGoal(goal: goal)
                    }
                }
                )
            }
        }
    }
}

// A small example of using this popup
// You probably won't need the @Previewable
#Preview {
    @Previewable @State var showingEditPopup = false
    
    
    VStack(spacing: 0) {
        Button("Edit Goal"){
            showingEditPopup = true
        }
        .buttonStyle(PurpleButtonStyle(active: false))
    }
    .frame(width: 999, height: 999)
    .background(.gray)
    .task {
        await ApiCall.shared.refreshGoals()
    }
    .overlay{
        if showingEditPopup {
            let goal = GoalItemBuilder()
                .title("Go to the gym 3 times a week.")
                .category("Fitness")
                .due(Date(timeIntervalSinceNow: 10000))
                .mon().wed().fri()
                .id(4)
                .build()
            EditGoalView(goal: ApiCall.shared.goals.last ?? goal,
                isShowing: $showingEditPopup)
        }
    }
    }
