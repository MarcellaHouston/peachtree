//
//  EditGoalView.swift
//  Reach
//
//  Created by Marcella Houston on 3/17/26.
//

import SwiftUI

struct EditGoalView: View {
    @State private var goal = GoalItemBuilder()
        .title("Go to the gym 3 times a week.")
        .category("Fitness")
        .due(Date(timeIntervalSinceNow: 1000))
        .mon().wed().fri()
        .build()
    
    var body: some View {
        VStack(spacing: 0) {
            // Title and pause area
            HStack{
                Text(goal.title).SmallHeader()
                Button(goal.isPaused ? "Unpause" : "Pause") {
                    goal.isPaused.toggle()
                }
                .buttonStyle(PurpleButtonStyle(active: goal.isPaused))

            }
            
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
                                
                            }
                            .buttonStyle(PurpleButtonStyle(active: true))
                        }
                        Button("Other") {
                            
                        }
                        .buttonStyle(PurpleButtonStyle(active: false))
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
                    Button(goal.due?.formatted(date: .abbreviated, time: .omitted) ?? "None"){
                        
                    }
                    .buttonStyle(PurpleButtonStyle(active: goal.due != nil))
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
                    
                }
                .buttonStyle(PurpleButtonStyle(active: false))
                Button("Cancel") {
                    
                }
                .buttonStyle(PurpleButtonStyle(active: false))
                Button("Save Changes") {
                    
                }
                .buttonStyle(PurpleButtonStyle(active: true))
            }
            .frame(height: 50)
        }
        .background(.white)
        .frame(maxHeight: 570)
        .cornerRadius(15)
    }
    
    
}

private extension Text {
    func SmallHeader() -> Self {
        self.bold()
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



#Preview {
    VStack(spacing: 0) {
        EditGoalView()
    }
    .frame(width: 999, height: 999)
    .background(.gray)
    }
