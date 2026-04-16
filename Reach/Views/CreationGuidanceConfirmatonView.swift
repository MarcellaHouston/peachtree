//
//  CreationGuidanceConfirmatonView.swift
//  Reach
//
//  Created by Rola Owaduge on 4/16/26.
//

import SwiftUI

struct CreationGuidanceConfirmatonView: View {
    @State private var loading = false
    @State private var isShowing = true
    @State private var showGuidance = false
    
    var body: some View {
        VStack(spacing: 0) {
            // Frame Title area
            Text("AI Assisted Goal Guidance")
                .font(.title)
                .padding(.vertical, 20)
            Text("Let’s set you up for success!")
                .SmallHeader()
                .padding(.bottom, 10)
            Text("If you'd like, I can help you refine this goal using insights from your past performance. Would you like to share your vision for this goal?")
                .padding(10)
            
            
            // --- LOADING OR BUTTONS ---
            if loading && ApiCall.shared.isCreatingGoal{
                VStack {
                    ProgressView()
                        .tint(.purple)
                    Text("Syncing with backend...")
                        .font(.caption)
                        .padding(.top, 8)
                
                }
                .padding(.bottom, 30)
            }
            else if (!loading){
                HStack(spacing: 20) {
                    Button("Yes, please!") {
                        // (Logic from above goes here)
                        loading = true
                    }
                    .buttonStyle(PurpleButtonStyle(active: true))

                    Button("No, thanks!") {
                        isShowing = false
                    }
                    .buttonStyle(PurpleButtonStyle(active: false))
                }
                .padding(.bottom, 30)
            }
            else {
                
            }
        }
        .frame(width: 360, height: 500)
        .background(.white)
        .cornerRadius(15)
        
    }
}

#Preview {
    CreationGuidanceConfirmatonView()
}
