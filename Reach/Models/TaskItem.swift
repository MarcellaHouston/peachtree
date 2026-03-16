//
//  TaskItem.swift
//  Reach
//
//  Created by Ismael Medina on 3/6/26.
//
import Foundation

//struct represents one task on the Today's Tasks screen
//stores task text and whether the user has completed it
//id used so program can display each task on the list
struct TaskItem: Identifiable {
    let id = UUID()
    let title: String
    var isCompleted: Bool
}
