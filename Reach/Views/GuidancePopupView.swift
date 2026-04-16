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
    var editMode: Bool
    var goalId: Int?
    
    init(goal: GoalItem, isShowing: Binding<Bool>, editMode: Bool = true, goalId: Int? = nil){
        // This is a copy because GoalItem is a struct, not a class
        self.goal = goal
        self._isShowing = isShowing
        self.editMode = editMode
        self.goalId = goalId
        
    }
    
    var body: some View {
        VStack(spacing: 0) {
            // Check if we should show the review screen or the mic screen
            if audioManager.showReview {
                reviewSection
            }
            else {
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
            if (editMode) {
                Text("Let's improve: \(goal.title)")
                    .SmallHeader()
                    .padding(.bottom, 10)
                Text("Tell me what aspects you’d like to change, and I can suggest adjustments based on your previous recaps.")
                    .padding(10)
            }
            else {
                Text("Let’s set you up for success!")
                    .SmallHeader()
                    .padding(.bottom, 10)
                Text("If you'd like, I can help you refine this goal using insights from your past performance. Would you like to share your vision for this goal?")
                    .padding(10)
            }
            
            // for goal creation, don't show mic until finished loading
            if (ApiCall.shared.isCreatingGoal) {
                VStack {
                    ProgressView()
                        .tint(.purple)
                    Text("Syncing with backend...")
                        .font(.caption)
                        .padding(.top, 8)
                
                }
                .padding(.bottom, 30)
            }
            // button connection to audio manager, starts recording when pressed
            else {
                Button(action: { audioManager.toggleRecording(at: .goalGuidance(goalId: goalId ?? goal.id)) }) {
                    Image(systemName: "mic.fill")
                        .font(.system(size: 35))
                        .foregroundColor(.white)
                        .frame(width: 80, height: 80)
                    // color changes based on audio manager state
                        .background(audioManager.isRecording ? .red : Color(red: 0.45, green: 0.35, blue: 0.65))
                        .clipShape(Circle())
                        .shadow(color: .black.opacity(0.1), radius: 4, x: 0, y: 4)
                }
                .padding(.top, 35)
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
            }
            
            // Footer with cancel button
            Button(editMode ? "Cancel" : "No, thanks!"){
                    isShowing = false
                }
                .buttonStyle(PurpleButtonStyle(active: false))
                .padding(.top, 20)
        
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
            
            // Summary of User's Wants
            Text("Wants:")
            Text(audioManager.summary)
            
            // Summary of LLM's Suggestions
            Text("Suggestions:")
            Text(audioManager.suggestedChanges["summary"] ?? "No summary available")

            Divider()
                .padding(10)
            
            
            // Goal Change suggestion
            // TODO: checkbox for each suggestion
            //Text(audioManager.suggestedChanges["name"] ?? "No summary available")
            SuggestionCheckbox(suggestion: audioManager.suggestedChanges["name"] ?? "")
            SuggestionCheckbox(suggestion: audioManager.suggestedChanges["end_date"] ?? "")
            SuggestionCheckbox(suggestion: audioManager.suggestedChanges["days_of_week"] ?? "")
            
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
            .padding(.top, 20)
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
                isShowing: $showingGGPopup, editMode: false)
        }
    }
    }
