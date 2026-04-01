//
//  TaskProgressBar.swift
//  Reach
//
//  Created by Marcella Houston on 3/31/26.
//

import SwiftUI

struct TaskProgressBar : View {
    let completedTaskCount: Int
    let totalTaskCount: Int
    private var progressWidth: CGFloat {
        if totalTaskCount == 0 {
            return 0
        }
        return 250 * CGFloat(completedTaskCount) / CGFloat(totalTaskCount)
    }
    
    var body: some View {
        VStack(spacing: 8) {
            Text("\(completedTaskCount)/\(totalTaskCount) tasks completed")
                .font(.system(size: 16, weight: .regular))
                .foregroundColor(.black)
            
            //outer capsule forms the base of the progress bar
            //a lighter purple capsule sits inside it as the background
            Capsule()
                .fill(Color.white)
                .frame(width: 264, height: 32)
                .overlay {
                    Capsule()
                        .fill(Color(red: 0.77, green: 0.69, blue: 0.94))
                        .padding(.horizontal, 6)
                        .padding(.vertical, 4)
                }
                //the darker purple capsule represents actual progress
                //its width changes dynamically based on completed tasks
                .overlay(alignment: .leading) {
                    Capsule()
                        .fill(Color(red: 0.52, green: 0.21, blue: 0.95))
                        .frame(width: progressWidth, height: 24)
                        .padding(.leading, 7)
                }
        }
        .padding(.top, 10)
        .padding(.bottom, 18)

    }
}
