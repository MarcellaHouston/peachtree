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
    
    //from Audiomanager.swift
    @State private var audioManager = AudioManager()
    
    var body: some View {
        // Scrollable content options
        
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
                        VStack(alignment: .center) {
                            // mic button
                            // hide button while the NLP is happening
                            if (!audioManager.isUploading) {
                                Button(action: { audioManager.toggleRecording(at: .nlp) }) {
                                    Image(systemName: "mic.fill")
                                        .font(.system(size: 20))
                                        .foregroundColor(.white)
                                        .frame(width: 35, height: 35)
                                    
                                        // color changes based on audio manager state
                                        .background(audioManager.isRecording ? .red : Color(red: 0.45, green: 0.35, blue: 0.65))
                                        .clipShape(Circle())
                                        .shadow(color: .black.opacity(0.1), radius: 4, x: 0, y: 4)
                                }
                                .buttonStyle(MicButtonStyle())
                            }
                            
                            // while waiting for LLM response, shows the user "Creating a plan"
                            if audioManager.isUploading {
                                ProgressView("Parsing your input...")
                                    .font(.system(size: 10, weight: .regular))
                                
                            // if user is still recording, displays this
                            } else if (audioManager.isRecording){
                                Text("Listening...")
                                    .font(.system(size: 10, weight: .regular))
                                    .foregroundColor(audioManager.isRecording ? .red : .black)
                            }
                        }
                        
                    }
                    .padding(.horizontal, 20)
                    Divider()
                        .padding(.horizontal, 20)
                        .padding(.bottom, 10)
                } else {
                    GoalGuidanceBar(prompt: "Thinking about adjusting this goal? Tap to receive goal guidance!")
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
        
        //to handle nlp data extracted
        
        .onChange(of: audioManager.extractedName) {
                if !audioManager.extractedName.isEmpty {
                    goal.title = audioManager.extractedName
                }
            }
        .onChange(of: audioManager.extractedDays) {
            if !audioManager.extractedDays.isEmpty {
                let days = audioManager.extractedDays.lowercased()
                goal.repeatDays.mon = days.contains("mon")
                goal.repeatDays.tue = days.contains("tue")
                goal.repeatDays.wed = days.contains("wed")
                goal.repeatDays.thu = days.contains("thu")
                goal.repeatDays.fri = days.contains("fri")
                goal.repeatDays.sat = days.contains("sat")
                goal.repeatDays.sun = days.contains("sun")
            }
        }
        
        .onChange(of: audioManager.extractedEndDate) {
            if !audioManager.extractedEndDate.isEmpty {
                //to convert string into date object
                let formatter = DateFormatter()
                formatter.dateFormat = "yyyy-MM-dd"
                
                if let decodedDate = formatter.date(from: audioManager.extractedEndDate) {
                    // change var to reflect our due date
                    goal.due = decodedDate
                    // Sync the UI DatePicker state
                    newEndDate = decodedDate
                } else {
                    //wrong format?
                    print("Failed to parse date: \(audioManager.extractedEndDate)")
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
