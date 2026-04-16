//
//  SuggestionCheckbox.swift
//  Reach
//
//  Created by Rola Owaduge on 4/3/26.
//

import SwiftUI

struct SuggestionCheckbox: View {
    let suggestion: String
    // Changed from @State to properties that are controlled by the parent
    let isSelected: Bool
    let onToggle: () -> Void
    
    var body: some View {
        HStack(spacing: 18) {
            Button {
                // Trigger the logic in ReviewSection (toggleSuggestion)
                onToggle()
            } label: {
                Rectangle()
                    .fill(isSelected ? Color(red: 0.42, green: 0.33, blue: 0.72) : Color.white)
                    .frame(width: 20, height: 20)
                    .overlay {
                        if isSelected {
                            Image(systemName: "checkmark")
                                .font(.system(size: 10, weight: .bold))
                                .foregroundColor(.white)
                        }
                    }
                    .overlay {
                        Rectangle()
                            .stroke(Color(red: 0.34, green: 0.33, blue: 0.39), lineWidth: 4.5)
                    }
            }
            .buttonStyle(.plain)
            
            Text(suggestion)
                .font(.body)
                .onTapGesture {
                    // Also toggle when tapping the text for better UX
                    onToggle()
                }
        }
    }
}

#Preview {
    // Preview with a dummy state
    SuggestionCheckbox(
        suggestion: "this is a checkbox",
        isSelected: true,
        onToggle: {}
    )
}
