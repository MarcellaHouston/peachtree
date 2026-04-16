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
                if ApiCall.shared.weeklyRecapSuggestions.isEmpty {
                    Text("There are no present AI suggestions")
                        .font(.system(size: 16))
                        .foregroundColor(.black)
                        .padding(.top, 30)
                } else {
                    VStack(spacing: 26) {
                        ForEach((0..<ApiCall.shared.weeklyRecapSuggestions.count), id: \.self) { i in
                            SuggestionRow(suggestion: ApiCall.shared.weeklyRecapSuggestions[i], ind: i)
                        }
                    }
                    .padding(.horizontal, 28)
                    .padding(.bottom, 140)
                }
            }
            
            HStack {
                Button("Cancel") {
                    isShowing = false
                }
                .buttonStyle(PurpleButtonStyle(active: false))
                Button("Save Changes") {
                    Task {
                        let didSave = await ApiCall.shared.receiveSuggestions(ApiCall.shared.selectedRecapSuggestions())
                        if didSave {
                            await ApiCall.shared.refreshGoals()
                            _ = await ApiCall.shared.refreshTasks()
                            isShowing = false
                        }
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
    let suggestion: [String: String]
    let ind: Int

    var body: some View {
        VStack {
            if let goalIdString = suggestion["goal_id"],
               let goalId = Int(goalIdString),
               let goal = ApiCall.shared.goals.first(where: { $0.id == goalId }) {
                Text(goal.title)
            }

            HStack(spacing: 18) {
                Button {
                    ApiCall.shared.toggleWeeklyRecapSuggestion(ind: ind)
                } label: {
                    Rectangle()
                        .fill(
                            ApiCall.shared.selectedWeeklyRecapSuggestions[ind]
                                ? Color(red: 0.42, green: 0.33, blue: 0.72)
                                : Color.white
                        )
                        .frame(width: 40, height: 40)
                        .overlay {
                            if ApiCall.shared.selectedWeeklyRecapSuggestions[ind] {
                                Image(systemName: "checkmark")
                                    .font(.system(size: 22, weight: .bold))
                                    .foregroundColor(.white)
                            }
                        }
                        .overlay {
                            if !ApiCall.shared.selectedWeeklyRecapSuggestions[ind] {
                                Rectangle()
                                    .stroke(Color(red: 0.34, green: 0.33, blue: 0.39), lineWidth: 4.5)
                            }
                        }
                }
                .buttonStyle(.plain)

                Button {
                    // Nothing
                } label: {
                    HStack(spacing: 0) {
                        Spacer(minLength: 0)

                        Text(suggestion["summary"] ?? "")
                            .font(.system(size: 15, weight: .regular))
                            .foregroundColor(.black)
                            .multilineTextAlignment(.center)
                            .fixedSize(horizontal: false, vertical: true)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 10)

                        Spacer(minLength: 0)
                    }
                    //.frame(minHeight: 46)
                    .frame(minHeight: 72)
                    .frame(maxWidth: .infinity)
                    .background(Color(red: 0.77, green: 0.69, blue: 0.94))
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                }
                .buttonStyle(.plain)
            }
        }
    }
}
