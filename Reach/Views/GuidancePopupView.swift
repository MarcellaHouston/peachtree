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
            Text(audioManager.changesSummary)

            Divider()
                .padding(10)
            
            
            // Goal Change suggestion
            // TODO: checkbox for each suggestion
            //Text(audioManager.suggestedChanges["name"] ?? "No summary available")
            // Individual Suggestion Checkboxes
            VStack(alignment: .leading, spacing: 16) {
                ForEach(audioManager.suggestedChanges.indices, id: \.self) { index in
                    let suggestion = audioManager.suggestedChanges[index]
                    
                    if let summaryText = suggestion["summary"], !summaryText.isEmpty {
                        VStack(alignment: .leading, spacing: 6) {
                            Text(getLabel(for: suggestion))
                                .font(.caption)
                                .foregroundColor(.secondary)
                                .textCase(.uppercase)
                            
                            SuggestionCheckbox(
                                suggestion: summaryText,
                                isSelected: isSuggestionSelected(suggestion),
                                onToggle: { toggleSuggestion(suggestion) }
                            )
                        }
                    }
                }
            }
            .padding(.horizontal)
            
            // Footer with Cancel & Confirm buttons
            HStack {
                Button("Cancel") {
                    isShowing = false
                }
                .buttonStyle(PurpleButtonStyle(active: false))
                Button("Save Changes") {
                    print("DEBUG: Save Changes tapped. Applying \(ApiCall.shared.goalMods.count) modifications.")
                    isShowing = false
                    Task {
                        await ApiCall.shared.applyGoalMods()
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
    
    // MARK: - Helper Functions
    func getLabel(for suggestion: [String: String]) -> String {
            if suggestion["name"] != nil { return "Change name to:" }
            if suggestion["end_date"] != nil { return "Change end date to:" }
            if suggestion["days_of_week"] != nil { return "Change schedule to:" }
            if suggestion["difficulty"] != nil { return "Change difficulty to:" }
            return "Suggested change:"
        }

        /// Checks if this specific suggestion is already in the global goalMods list
        func isSuggestionSelected(_ suggestion: [String: String]) -> Bool {
            let key = getModificationKey(for: suggestion)
            // Check ApiCall.shared.goalMods for a match with this goal's ID and the specific field key
            return ApiCall.shared.goalMods.contains { $0.id == goal.id && $0.key == key }
        }

        /// Toggles the modification in the global ApiCall.shared.goalMods list
        func toggleSuggestion(_ suggestion: [String: String]) {
            let key = getModificationKey(for: suggestion)
            
            if isSuggestionSelected(suggestion) {
                // If it exists, remove it (uncheck)
                print("DEBUG: Removing modification for key: \(key)")
                ApiCall.shared.removeMod(goalId: goal.id, key: key)
            } else {
                // Find the suggested value (e.g., the actual new name or date)
                let dataKeys = ["name", "end_date", "days_of_week", "difficulty"]
                for k in dataKeys {
                    if let val = suggestion[k] {
                        print("DEBUG: Adding modification - Key: \(k), Value: \(val)")
                        // Map "end_date" to your internal ".due" key
                        let modKey: GoalModification.Key = (k == "end_date") ? .due : key
                        let newMod = GoalModification(id: goal.id, key: modKey, val: val)
                        ApiCall.shared.addMod(newMod)
                        break
                    }
                }
            }
        }

        func getModificationKey(for suggestion: [String: String]) -> GoalModification.Key {
            if suggestion["name"] != nil { return .title }
            if suggestion["end_date"] != nil { return .due }
            if suggestion["days_of_week"] != nil { return .repeatDays }
            if suggestion["difficulty"] != nil { return .difficulty }
            return .title
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
