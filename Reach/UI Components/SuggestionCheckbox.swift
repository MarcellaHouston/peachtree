//
//  SuggestionCheckbox.swift
//  Reach
//
//  Created by Rola Owaduge on 4/3/26.
//

import SwiftUI

struct SuggestionCheckbox: View {
    let suggestion: String
    @State private var selected = false
    
    var body: some View {
        HStack(spacing: 18) {
            //checkbox button on the left
            //tapping it toggles whether the task is completed
            Button {
                selected.toggle()
            } label: {
                Rectangle()
                    .fill(selected ? Color(red: 0.42, green: 0.33, blue: 0.72) : Color.white)
                    .frame(width: 20, height: 20)
                    //if the task is completed a checkmark is displayed
                    .overlay {
                        if selected {
                            Image(systemName: "checkmark")
                                .font(.system(size: 10, weight: .bold))
                                .foregroundColor(.white)
                        }
                    }
                    //if the task is not completed a dark border outlines the square
                    .overlay {
                            Rectangle()
                                .stroke(Color(red: 0.34, green: 0.33, blue: 0.39), lineWidth: 4.5)
                    }
            }
            .buttonStyle(.plain)
            Text(suggestion)
        }
    }
}
#Preview {
        SuggestionCheckbox(suggestion: "this is a checkbox")
}
