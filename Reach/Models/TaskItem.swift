//
//  TaskItem.swift
//  Reach
//
//  Created by Ismael Medina on 3/6/26.
//
import Foundation

// Rrepresentation of a task on the Daily Goal Digest
struct TaskItem: Identifiable {
    var id: Int = -1
    let title: String
    var isCompleted: Bool
    
    func requestBody() -> [String:Any] {
        let body: [String:[String:Any]] = [
            "task": [
                "name": title,
                "id": id,
                "measurable": "completion",
                "end_date": NO_DUE,
                "user": STAFF_USER_ID // TODO: Unhardcode the user
                
                // No isCompleted in backend
            ]
        ]
        
        return body
    }
}

