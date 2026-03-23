//
//  TaskSchema.swift
//  Reach
//
//  Created by Marcella Houston on 3/23/26.
//

struct TaskSchema : Codable {
    var task: String
    var weekly_frequency: Int
    var weight: Int
    var days_of_week: String
    var start_date: String
    var end_date: String
    var impetus: Int
    
    func buildTask() -> TaskItem {
        return TaskItem(title: task, isCompleted: false)
    }
}
