//
//  FallbackData.swift
//  Reach
//
//  Created by Ismael Medina on 3/25/26.
//

import Foundation
//Backup data incase backend fails
enum FallbackData {
    //For Task Items
    static let fallbackTasks: [TaskItem] = [
        TaskItem(id: -101, title: "Went to the gym", isCompleted: false),
        TaskItem(id: -102, title: "Wrote a page in my journal", isCompleted: false),
        TaskItem(id: -103, title: "Studied for 2 hours", isCompleted: false),
        TaskItem(id: -104, title: "Applied to 5 jobs", isCompleted: false),
        TaskItem(id: -105, title: "Make a keto meal", isCompleted: false),
        TaskItem(id: -106, title: "Brushed my teeth", isCompleted: false)
    ]
    
    //For Goal Items
    static let fallbackGoals: [GoalItem] = [
        GoalItemBuilder().id(-201).title("Journal daily").build(),
        GoalItemBuilder().id(-202).title("Brush my teeth twice daily").build(),
        GoalItemBuilder().id(-203).title("Study 2 hours a day").build(),
        GoalItemBuilder().id(-204).title("Apply for 5 jobs a day").build(),
       // GoalItemBuilder().id(-205).title("Go to the gym 3 times a week").build(),
       // GoalItemBuilder().id(-206).title("Cook healthy meals").build()
    ]
    
    static let fallbackGoalMods: [GoalModification] = [
        GoalModification(id: -201, key: .category, val: "Health"),
        GoalModification(id: -201, key: .title, val: "Journal for 5m daily"),
        GoalModification(id: -202, key: .difficulty, val: "hard"),
        GoalModification(id: -203, key: .title, val: "Study 1 hour a day")
    ]
    
    //For Task Goal Names in Edit Goal Popup
    static let fallbackTaskGoalNames: [Int: String] = [
        -101: "Go to the gym 3 times a week",
        -102: "Journal daily",
        -103: "Study 2 hours a day",
        -104: "Apply for 5 jobs a day",
        -105: "Cook healthy meals",
        -106: "Brush my teeth twice daily"
    ]
}
