//
//  GuidancePopupView.swift
//  Reach
//
//  Created by Rola Owaduge on 3/31/26.
//

import SwiftUI
import AVFoundation

struct GuidancePopupView: View {
    @State private var goal: GoalItem
    //from Audiomanager.swift
    @State private var audioManager = AudioManager()

    @Binding var isShowing: Bool
    
    init(goal goalIn: GoalItem, isShowing isShowingIn: Binding<Bool>){
        // This is a copy because GoalItem is a struct, not a class
        goal = goalIn
        _isShowing = isShowingIn
    }
    
    var body: some View {
        VStack(spacing: 0) {
            // Check if we should show the review screen or the mic screen
            if audioManager.showReview {
                reviewSection
            } else {
                recordingSection
            }
        }
    }
    
    // Recording pop-up for goal guidance
    var recordingSection: some View {
        VStack(spacing: 0) {
            
            // Frame Title area
            Text("AI Assisted Goal Guidance")
                .font(.title)
                .padding(.vertical, 20)
            
            Text("Let's improve: \(goal.title)")
                .SmallHeader()
                .padding(.bottom, 10)
            Text("Tell me what aspects you’d like to change, and I can suggest adjustments based on your previous recaps.")
                .padding(10)
            
            // button connection to audio manager, starts recording when pressed
            Button(action: { audioManager.toggleRecording() }) {
                Image(systemName: "mic.fill")
                    .font(.system(size: 35))
                    .foregroundColor(.white)
                    .frame(width: 80, height: 80)
                
                    // color changes based on audio manager state
                    .background(audioManager.isRecording ? .red : Color(red: 0.45, green: 0.35, blue: 0.65))
                    .clipShape(Circle())
                    .shadow(color: .black.opacity(0.1), radius: 4, x: 0, y: 4)
            }
            .padding(.top, 50)
            .buttonStyle(MicButtonStyle())
            
            // while waiting for LLM response, shows the user "Creating a plan"
            if audioManager.isUploading {
                ProgressView("Creating a plan...")
                    .padding(.top, 20)
                
                //if user is still recording, displays this
            } else {
                Text(audioManager.isRecording ? "Listening..." : "Press to begin to speak")
                    .font(.system(size: 20, weight: .regular))
                    .foregroundColor(audioManager.isRecording ? .red : .black)
                    .padding(.top, 24)
            }
            
            // Footer with cancel button
                Button("Cancel"){
                    isShowing = false
                }
                    .buttonStyle(PurpleButtonStyle(active: false))
        }
        .frame(width: 360, height: 500)
        .background(.white)
        .cornerRadius(15)
    }
    
    // summary and suggested goal changes
    var reviewSection: some View {
        VStack(spacing: 0) {
            // Frame Title area
            Text("AI Assisted Goal Guidance")
                .font(.title)
                .padding(.vertical, 20)
            
            Text("Wants:")
            // TODO: change to reflect backend schema for GG
            Text(audioManager.summary)
            Text("Suggestions:")
            // Text(audioManager.suggestions)
            Divider()
                .padding(10)
            
            
            // Goal Change suggestion
            // TODO: checkbox for each suggestion
            SuggestionCheckbox(suggestion: "Maybe do something else")
            
            
            // Footer with Cancel & Confirm buttons
            HStack {
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
        }
        .frame(width: 360, height: 500)
        .background(.white)
        .cornerRadius(15)
    }
    
}


// A small example of using this popup
// You probably won't need the @Previewable
#Preview {
    @Previewable @State var showingGGPopup = false
    
    
    VStack(spacing: 0) {
        Button("Goal Guidance"){
            showingGGPopup = true
        }
        .buttonStyle(PurpleButtonStyle(active: false))
    }
    .frame(width: 999, height: 999)
    .background(.gray)
    .task {
        await ApiCall.shared.refreshGoals()
    }
    .overlay{
        if showingGGPopup {
            let goal = GoalItemBuilder()
                .title("Go to the gym 3 times a week.")
                .category("Fitness")
                .due(Date(timeIntervalSinceNow: 10000))
                .mon().wed().fri()
                .id(4)
                .build()
            GuidancePopupView(goal: ApiCall.shared.goals.last ?? goal,
                isShowing: $showingGGPopup)
        }
    }
    }
