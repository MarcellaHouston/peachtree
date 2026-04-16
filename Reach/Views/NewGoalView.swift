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
    @State private var showGuidance = false
    
    
    @Binding var isShowing: Bool    
    
    var body: some View {
        VStack(spacing: 0) {
            
            // Frame Title area
            Text("Create a New Goal")
                .font(.title)
                .padding(.vertical, 20)
            
            GoalOptions(goal: $goal, editMode: false)
            
            // Footer with cancel and confirm buttons
            HStack {
                Spacer()
                Button("Cancel"){
                    isShowing = false
                }
                    .buttonStyle(PurpleButtonStyle(active: false))
                Button("Create Goal") {
                    
                    // Post goal to the backend
                    Task {
                        await ApiCall.shared.createGoal(goal: goal)
                    }
                    
                    //isShowing = false
                    // guidance popup should eventually pass in goal info to GuidancePopupView
                    showGuidance = true
                    
                                        
                }
                .buttonStyle(PurpleButtonStyle(active: true))
            }
            .frame(height: 50)
            .padding(.horizontal, 20)
        }
        .background(.white)
        .frame(maxWidth: 360, maxHeight: 500)
        .cornerRadius(15)
        .fullScreenCover(isPresented: $showGuidance,
                                 onDismiss: didDismiss) {
            let goal = GoalItemBuilder()
                .title("Go to the gym 3 times a week.")
                .category("Fitness")
                .due(Date(timeIntervalSinceNow: 10000))
                .mon().wed().fri()
                .id(4)
                .build()
            GuidancePopupView(goal: ApiCall.shared.goals.last ?? goal,
                              isShowing: $showGuidance, editMode: false)
            .frame(maxWidth: .infinity,
                   maxHeight: .infinity)
            .background(Color.black)
            .ignoresSafeArea(edges: .all)
        }
    }
    func didDismiss() {
        showGuidance = false
        isShowing = false
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
