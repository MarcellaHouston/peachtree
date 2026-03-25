//
//  EditGoalView.swift
//  Reach
//
//  Created by Marcella Houston on 3/17/26.
//

import SwiftUI

struct EditGoalView: View {
    @State private var goal: GoalItem
    @State private var newEndDate = Date()
    @State private var showingDatePicker = false
    
    @State private var newCategory = ""
    @State private var showingCategoryField = false
    
    @State private var showingPausePopup = false
    @State private var showingDeletePopup = false
    
    // Store some @State variable wherever you call an EditGoalView
    // When you call init, set isShowingIn: $variable
    @Binding var isShowing: Bool
    
    init(goal goalIn: GoalItem, isShowing isShowingIn: Binding<Bool>){
        // This is a copy because GoalItem is a struct, not a class
        goal = goalIn
        // Add a leading _ to
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
            
            // Scrollable content options
            ScrollView {
                VStack(alignment: .leading) {
                    // Goal guidance spot
                    HStack {
                        Circle()
                            .frame(width: 34)
                        Text("Thinking about adjusting this goal? Tap to receive goal guidance!")
                    }
                    .onTapGesture {
                        // TODO: Navigate to goal guidance
                    }
                    
                    // Goal category spot
                    Text("Goal Category").SmallHeader()
                    HStack {
                        if let cat = goal.category {
                            Button(cat) {
                                goal.category = nil
                            }
                            .buttonStyle(PurpleButtonStyle(active: true))
                        }
                        Button("Other") {
                            showingCategoryField.toggle()
                        }
                        .buttonStyle(PurpleButtonStyle(active: false))
                        if showingCategoryField {
                            TextField("Enter new category", text: $newCategory)
                            Button("Set") {
                                showingCategoryField = false
                                goal.category = newCategory
                            }
                            .buttonStyle(PurpleButtonStyle(active: true))
                        }
                    }
                    
                    // Difficulty spot
                    Text("Goal Difficulty").SmallHeader()
                    HStack {
                        Button("Easy") {
                            goal.difficulty = .easy
                        }
                        .buttonStyle(PurpleButtonStyle(active: goal.difficulty == .easy))
                        Button("Average") {
                            goal.difficulty = .average
                        }
                        .buttonStyle(PurpleButtonStyle(active: goal.difficulty == .average))
                        Button("Hard") {
                            goal.difficulty = .hard
                        }
                        .buttonStyle(PurpleButtonStyle(active: goal.difficulty == .hard))
                    }
                    
                    // Repeats spot
                    Text("Repeats").SmallHeader()
                    HStack {
                        Button("S") {
                            goal.repeatDays.sun.toggle()
                        }
                        .buttonStyle(PurpleButtonStyle(active: goal.repeatDays.sun))
                        Button("M") {
                            goal.repeatDays.mon.toggle()
                        }
                        .buttonStyle(PurpleButtonStyle(active: goal.repeatDays.mon))
                        Button("T") {
                            goal.repeatDays.tue.toggle()
                        }
                        .buttonStyle(PurpleButtonStyle(active: goal.repeatDays.tue))
                        Button("W") {
                            goal.repeatDays.wed.toggle()
                        }
                        .buttonStyle(PurpleButtonStyle(active: goal.repeatDays.wed))
                        Button("T") {
                            goal.repeatDays.thu.toggle()
                        }
                        .buttonStyle(PurpleButtonStyle(active: goal.repeatDays.thu))
                        Button("F") {
                            goal.repeatDays.fri.toggle()
                        }
                        .buttonStyle(PurpleButtonStyle(active: goal.repeatDays.fri))
                        Button("S") {
                            goal.repeatDays.sat.toggle()
                        }
                        .buttonStyle(PurpleButtonStyle(active: goal.repeatDays.sat))
                    }
                    
                    // Ends on spot
                    Text("Ends On").SmallHeader()
                    HStack{
                        Button(goal.due?.formatted(date: .abbreviated, time: .omitted) ?? "Never"){
                            if goal.due != nil{
                                goal.due = nil
                            }else{
                                showingDatePicker.toggle()
                            }
                        }
                        .buttonStyle(PurpleButtonStyle(active: goal.due != nil))
                        if showingDatePicker && goal.due == nil {
                            DatePicker(
                                "New Date:",
                                selection: $newEndDate,
                                displayedComponents: [.date]
                            )
                            Button("Set"){
                                showingDatePicker = false
                                goal.due = newEndDate
                            }
                            .buttonStyle(PurpleButtonStyle(active: true))
                        }
                    }
                }
            }
            .padding(.horizontal, 10)
            .padding(.top, 10)
            .padding(.bottom, 14)
            .frame(width: 360)
            .background(.white)
            
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
                    // TODO: Ensure this works when backend fixes it
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
                    // TODO: Make sure this works when backend implements pausing
                    Task {
                        await ApiCall.shared.snoozeGoal(goal: goal)
                    }
                }
                )
            }
        }
    }
}

// Reusable view for any kind of confirmation popup
// Automatically closes self upon hitting cancel or confirm
private struct ConfirmPopup: View {
    @Binding var isShown: Bool // Pass a variable like '$showingPopup' to bind
    
    let prompt: String
    let desc: String
    
    let confirm: String
    let effect: () -> Void
    
    var body: some View {
        VStack(spacing: 0) {
            Text(prompt).BigHeader()
            Text(desc)
            HStack{
                Button("Cancel") {
                    isShown = false
                }
                .buttonStyle(PurpleButtonStyle(active: false))
                Button(confirm) {
                    effect()
                    isShown = false
                }
                .buttonStyle(PurpleButtonStyle(active: true))
            }
        }
        .frame(width: 310)
        .background(.white)
        .cornerRadius(15)
    }
}

private extension Text {
    func SmallHeader() -> Self {
        self.bold()
    }
    func BigHeader() -> Self {
        self.font(.system(size: 32, weight: .regular))
    }
}

private struct PurpleButtonStyle: ButtonStyle {
    let active: Bool

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .padding(.horizontal, 10)
            .padding(.vertical, 2)
            .background(active ? Color(red: 0.77, green: 0.69, blue: 0.94) : .white)
            .clipShape(.capsule)
            .frame(minWidth: 24, minHeight: 24)
            .overlay{
                if !active{
                    RoundedRectangle(cornerRadius: 10)
                        .stroke(.gray, lineWidth: 0.6)
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
        // goal = ApiCall.shared.goals.last ?? goal
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
