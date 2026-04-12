//
//  TodayTasksView.swift
//  Reach
//
//  Created by Ismael Medina on 3/6/26.
//

import SwiftUI

//this view builds the entire today’s tasks screen
//it combines the header, the list of tasks, the progress section, and the bottom navigation
//the tasks are stored in state so the UI updates automatically when a task is toggled
struct TodayTasksView: View {
    
    @Binding var appState: AppState
    let onAccountTap: () -> Void
    //Popup Code
    @State private var selectedGoal: GoalItem? = nil
    //dictionary mapping of task id to goal name
    @State private var selectedTaskGoalName: [Int: String] = [:]
    //controls whether the popup is visible or not
    @State private var showEditGoal = false
    //For Demo Mode
    
    //this property counts how many tasks are currently completed
    //it filters the task list and returns the number of tasks marked as done
    private var completedTaskCount: Int {
        ApiCall.shared.tasks.filter { $0.isCompleted }.count
    }

    //this gives the filled width for the progress bar
    private var progressWidth: CGFloat {
        if ApiCall.shared.tasks.isEmpty {
            return 0
        }

        return 250 * CGFloat(completedTaskCount) / CGFloat(ApiCall.shared.tasks.count)
    }

    var body: some View {
        VStack(spacing: 0) {
            //header at the top of the screen containing the status bar and profile section
            HeaderView(appState: $appState, onAccountTap: onAccountTap)
            VStack(spacing: 0) {
                //screen title centered below the header
                //the larger font matches the emphasis shown in the figma design
                Text("Today’s Tasks")
                    .font(.system(size: 42, weight: .regular))
                    .foregroundColor(.black)
                    .frame(maxWidth: .infinity)
                    .multilineTextAlignment(.center)
                    .padding(.top, 48)
                    .padding(.bottom, 34)

                //task list section
                //each task is generated dynamically from the tasks array
                //using bindings allows each row to modify the task state directly
                //only this section scrolls so the progress area stays in place
                ScrollView(showsIndicators: true) {
                    VStack(spacing: 26) {
                        //loops through each task and creates UI row fo each one
                        ForEach(ApiCall.shared.tasks) { task in
                            TodayTaskRow(task: task, onTaskTap: {
                                //when task is tapped, finds its goal
                                if let goalName = selectedTaskGoalName[task.id] {
                                    //find matching goal from backenddata
                                    if let matchedGoal =
                                        ApiCall.shared.goals.first(where: { $0.title == goalName }) {

                                        selectedGoal = matchedGoal
                                        showEditGoal = true
                                    }
                                }
                            })
                        }
                    }
                    .padding(.horizontal, 28)
                    .padding(.bottom, 140)
                }
                //frame fills remaining space
                .frame(maxWidth: .infinity, maxHeight: .infinity)

                //progress section that shows how many tasks have been completed
                //includes a text summary and a visual progress bar
                VStack(spacing: 8) {
                    Text("\(completedTaskCount)/\(ApiCall.shared.tasks.count) tasks completed")
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
            //this section fills the remaining screen space with the light background color
            //it visually separates the task area from the header and navigation bar
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            .background(Color(red: 0.93, green: 0.93, blue: 0.93))

            //bottom navigation bar for switching between major app sections
            BottomNavView(selectedTab: $appState.selectedTab)
        }
        //black background ensures the header and navigation bar blend into the edges of the screen
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .background(Color.black)
        .ignoresSafeArea(edges: .bottom)
        
        //API Call .task
        .task {
            //API Call
            await ApiCall.shared.refreshGoals()
            let didLoadTasks = await ApiCall.shared.refreshTasks()
            

            //REMOVE ONLY FOR DEBUGGING
            //print("=== TASKS IN VIEW ===")
            //for task in tasks {
          //      print("ID: \(task.id), TITLE: \(task.title)")
         //   }
            //REMOVE ONLY FOR DEBUGGING
        }
        //gray scale then popup appears
        .overlay {
            if showEditGoal, let selectedGoal = selectedGoal {
                Color.black.opacity(0.35)
                    .ignoresSafeArea()

                VStack {
                    Spacer()

                    EditGoalView(goal: selectedGoal, isShowing: $showEditGoal)

                    Spacer()
                }
            }
            
        }
    }
}

//this helper builds one task row
//the square on the left toggles the task and the purple button shows the task text
private struct TodayTaskRow: View {
    var task: TaskItem
    let onTaskTap: () -> Void

    var body: some View {
        HStack(spacing: 18) {
            //checkbox button on the left
            //tapping it toggles whether the task is completed
            Button {
                Task {
                    await ApiCall.shared.toggleTask(task: task)
                }
            } label: {
                Rectangle()
                    .fill(task.isCompleted ? Color(red: 0.42, green: 0.33, blue: 0.72) : Color.white)
                    .frame(width: 40, height: 40)
                    //if the task is completed a checkmark is displayed
                    .overlay {
                        if task.isCompleted {
                            Image(systemName: "checkmark")
                                .font(.system(size: 22, weight: .bold))
                                .foregroundColor(.white)
                        }
                    }
                    //if the task is not completed a dark border outlines the square
                    .overlay {
                        if !task.isCompleted {
                            Rectangle()
                                .stroke(Color(red: 0.34, green: 0.33, blue: 0.39), lineWidth: 4.5)
                        }
                    }
            }
            .buttonStyle(.plain)

            //task content button
            //this displays the task name inside the purple rounded rectangle
            Button {
                onTaskTap()
            } label: {
                HStack(spacing: 0) {
                    //spacers keep the text centered within the button
                    Spacer(minLength: 0)

                    Text(task.title)
                        .font(.system(size: 15, weight: .regular))
                        .foregroundColor(.black)
                        .lineLimit(1)

                    Spacer(minLength: 0)

                    //chevron icon indicates that tapping the task may lead to more details
                    Image(systemName: "chevron.right")
                        .font(.system(size: 14, weight: .bold))
                        .foregroundColor(.black)
                        .padding(.trailing, 16)
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

/*
#Preview {
    TodayTasksView(appState: .constant(AppState(selectedTab: .todayTasks, showSignIn: false, isDemoMode: true, showDemoPopup: true)))
}
*/

#Preview {TodayTasksView(appState: .constant(AppState(selectedTab: .todayTasks, showSignIn: false, isDemoMode: true, showDemoPopup: true)), onAccountTap: {})
}
