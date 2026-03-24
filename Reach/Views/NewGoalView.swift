//
//  NewGoalView.swift
//  Reach
//
//  Created by Rola Owaduge on 3/21/26.
//

import SwiftUI

struct NewGoalView: View {
    @State private var goal = GoalItem()
    @State private var newEndDate = Date()
    @State private var showingDatePicker = false
    
    @State private var newCategory = ""
    @State private var showingCategoryField = false
    
    
    @Binding var isShowing: Bool
    
    
    var body: some View {
        VStack(spacing: 0) {
            
            // Frame Title area
            Text("Create a New Goal")
                .font(.title)
                .padding(.vertical, 20)
            
            // Goal guidance spot
            HStack {
                Circle()
                    .frame(width: 34)
                Text("Not sure where to start with this goal? Tap to receive goal guidance!")
                    
            }
            .onTapGesture {
                // TODO: Navigate to goal guidance
            }
            .padding(.horizontal, 10)
            .padding(.bottom, 20)
            
            // Scrollable content options
            ScrollView {
                VStack(alignment: .leading) {
                    
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
                    
                    // Goal category spot
                    Text("Goal Category")
                        .SmallHeader()
                        .padding(.horizontal, 20)
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
                    .padding(.horizontal, 20)
                    .padding(.bottom, 10)
                    
                    // Difficulty spot
                    Text("Goal Difficulty")
                        .SmallHeader()
                        .padding(.horizontal, 20)
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
                    .padding(.horizontal, 20)
                    .padding(.bottom, 10)
                    
                    // Repeats spot
                    Text("Repeats")
                        .SmallHeader()
                        .padding(.horizontal, 20)
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
                    .padding(.horizontal, 20)
                    .padding(.bottom, 10)
                    
                    // Ends on spot
                    Text("Ends On")
                        .SmallHeader()
                        .padding(.horizontal, 20)
                    
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
                    .padding(.horizontal, 20)
                }
            }
            .background(.white)
            
            // Footer with cancel and confirm buttons
            HStack {
                Spacer()
                Button("Cancel"){
                    isShowing = false
                }
                    .buttonStyle(PurpleButtonStyle(active: false))
                Button("Create Goal") {
                    // TODO: Inform the backend
                    isShowing = false
                }
                .buttonStyle(PurpleButtonStyle(active: true))
            }
            .frame(height: 50)
            .padding(.horizontal, 20)
        }
        .background(.white)
        .frame(maxWidth: 360, maxHeight: 570)
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
    @Previewable @State var showingNewPopup = true
    //@Previewable @State var showingNewPopup = false
    
    VStack(spacing: 0) {
        Button("+"){
            showingNewPopup = true
        }
        .buttonStyle(PurpleButtonStyle(active: false))
    }
    .frame(width: 999, height: 999)
    .background(.gray)
    .overlay{
        if showingNewPopup {
            NewGoalView(isShowing: $showingNewPopup)
        }
    }
}
