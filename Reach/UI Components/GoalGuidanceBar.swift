//
//  GoalGuidanceBar.swift
//  Reach
//
//  Created by Marcella Houston on 3/27/26.
//

import SwiftUI

struct GoalGuidanceBar: View {
    let prompt: String
    @State private var isPresenting = false
    var goal: GoalItem
    
    var body: some View {
        HStack {
            Button {
                isPresenting = true
            } label: {
                Circle()
                    .fill(Color(red: 0.50, green: 0.37, blue: 0.77))
                    .frame(width: 50, height: 50)
                    .overlay {
                        //public library for plus
                        Image(systemName: "sparkles")
                            .font(.system(size: 25, weight: .regular))
                            .foregroundColor(.white)
                    }
            }
            .buttonStyle(.plain)
            
                        
            Text(prompt)
        }
        .task {
            await ApiCall.shared.refreshGoals()
        }
        .fullScreenCover(isPresented: $isPresenting,
                                 onDismiss: didDismiss) {
            GuidancePopupView(goal: goal,
                              isShowing: $isPresenting)
            .frame(maxWidth: .infinity,
                   maxHeight: .infinity)
            .background(Color.black)
            .ignoresSafeArea(edges: .all)
        }
    }


    func didDismiss() {
        isPresenting = false
    }
    
}

#Preview {
        GoalGuidanceBar(prompt: "this is a sample prompt. do you want a suggestion?", goal: GoalItem(title: "this is a sample goal"))
}
