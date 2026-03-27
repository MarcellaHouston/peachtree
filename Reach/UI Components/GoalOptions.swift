//
//  GoalOptions.swift
//  Reach
//
//  Created by Marcella Houston on 3/27/26.
//

import SwiftUI

struct GoalOptions: View {
    @Binding var goal: GoalItem
    
    let editMode: Bool
    
    @State private var showingDatePicker = false
    @State private var newEndDate = Date()
    
    @State private var showingCategoryField = false
    @State private var newCategory = ""
    
    var body: some View {
        // Scrollable content options
        if !editMode {
            GoalGuidanceBar(prompt: "Not sure where to start with this goal? Tap to receive goal guidance!") {
                // TODO: Navigate to goal creation guidance
            }
            .padding(.horizontal, 10)
            .padding(.bottom, 20)
        }
        ScrollView {
            VStack(alignment: .leading) {
                
                if !editMode {
                    // Goal title spot
                    Text("Goal Title")
                        .SmallHeader()
                        .padding(.horizontal, 20)
                    
                        
                    
                    HStack(alignment: .bottom){
                        VStack(alignment: .leading) {
                            Text("Type or say your goal here")
                                .foregroundStyle(.secondary)
                                .padding(.bottom, -5)
                            TextField("E.g. Read 10 pages a day", text: $goal.title)
                        }
                        Circle()
                            .frame(width: 34)
                            
                    }
                    .padding(.horizontal, 20)
                    Divider()
                        .padding(.horizontal, 20)
                        .padding(.bottom, 10)
                } else {
                    GoalGuidanceBar(prompt: "Thinking about adjusting this goal? Tap to receive goal guidance!") {
                        // TODO: Navigate to goal guidance
                    }
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
    }
}
