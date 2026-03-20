//
//  TaskItem.swift
//  Reach
//
//  Created by Ismael Medina on 3/6/26.
//
import Foundation

//struct represents one task on the Today's Tasks screen
//id gives each task in taskitem struct its own id, makes it easier to iterate and change specific taskitem elements
//title is the task text for each taskitem
//isCompleted is used to check whether a checkmark has been checked or not (True ? False)
struct TaskItem: Identifiable {
    let id = UUID()
    let title: String
    var isCompleted: Bool
}
