//
//  GoalSuggestionsPopup.swift
//  Reach
//
//  Created by Marcella Houston on 4/2/26.
//

import SwiftUI

struct GoalSuggestionsPopup : View {
    @Binding var isShowing: Bool // Pass a variable like '$showingPopup' to bind
    
    var body: some View {
        VStack(spacing: 0) {
            Text("Do you want to add these AI suggestions?").SmallHeader()
                .padding(.vertical, 10)
            Spacer()
            ScrollView(showsIndicators: true) {
                VStack(spacing: 26) {
                    ForEach((0..<ApiCall.shared.goalMods.count), id: \.self) { i in
                        SuggestionRow(suggestion: ApiCall.shared.goalMods[i], ind: i)
                    }
                }
                .padding(.horizontal, 28)
                .padding(.bottom, 140)
            }
            
            HStack {
                Button("Cancel") {
                    isShowing = false
                }
                .buttonStyle(PurpleButtonStyle(active: false))
                Button("Save Changes") {
                    isShowing = false
                    Task {
                        await ApiCall.shared.applyGoalMods()
                    }
                }
                .buttonStyle(PurpleButtonStyle(active: true))
            }
            .frame(height: 50)

        }
        .frame(width: 360)
        .frame(maxHeight: 570)
        .background(.white)
        .cornerRadius(15)

    }
}

#Preview {
    @Previewable @State var showingPopup = true
    
    
    VStack(spacing: 0) {
        Button("Get Suggestions"){
            showingPopup = true
        }
        .buttonStyle(PurpleButtonStyle(active: false))
    }
    .frame(width: 999, height: 999)
    .background(.gray)
    .task {
        //await ApiCall.shared.refreshGoals()
    }
    .overlay{
        if showingPopup {
            GoalSuggestionsPopup(isShowing: $showingPopup)
            Button("Load test data") {
                ApiCall.shared.fallback()
            }
        }
    }
}

private struct SuggestionRow: View {
    let suggestion: GoalModification
    let ind: Int

    var body: some View {
        VStack {
            Text(ApiCall.shared.goalOf(id: suggestion.id).title)
            HStack(spacing: 18) {
                //checkbox button on the left
                //tapping it toggles whether the task is completed
                Button {
                    ApiCall.shared.toggleMod(ind: ind)
                } label: {
                    Rectangle()
                        .fill(suggestion.active ? Color(red: 0.42, green: 0.33, blue: 0.72) : Color.white)
                        .frame(width: 40, height: 40)
                    //if the task is completed a checkmark is displayed
                        .overlay {
                            if suggestion.active {
                                Image(systemName: "checkmark")
                                    .font(.system(size: 22, weight: .bold))
                                    .foregroundColor(.white)
                            }
                        }
                    //if the task is not completed a dark border outlines the square
                        .overlay {
                            if !suggestion.active {
                                Rectangle()
                                    .stroke(Color(red: 0.34, green: 0.33, blue: 0.39), lineWidth: 4.5)
                            }
                        }
                }
                .buttonStyle(.plain)
                
                //task content button
                //this displays the task name inside the purple rounded rectangle
                Button {
                    // Nothing
                } label: {
                    HStack(spacing: 0) {
                        //spacers keep the text centered within the button
                        Spacer(minLength: 0)
                        
                        Text(suggestion.toString())
                            .font(.system(size: 15, weight: .regular))
                            .foregroundColor(.black)
                            .lineLimit(1)
                        
                        Spacer(minLength: 0)
                    }
                    //rounded purple background for the task button
                    .frame(height: 46)
                    .frame(maxWidth: .infinity)
                    .background(Color(red: 0.77, green: 0.69, blue: 0.94))
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                }
                .buttonStyle(.plain)
            }
        }
    }
}
