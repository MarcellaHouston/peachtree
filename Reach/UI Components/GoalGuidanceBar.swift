//
//  GoalGuidanceBar.swift
//  Reach
//
//  Created by Marcella Houston on 3/27/26.
//

import SwiftUI

struct GoalGuidanceBar: View {
    let prompt: String
    let clickHandler: () -> Void
    
    var body: some View {
        HStack {
            Circle()
                .frame(width: 34)
            Text(prompt)
        }
        .onTapGesture {
            clickHandler()
        }
    }
}
