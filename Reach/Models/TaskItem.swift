//
//  TaskItem.swift
//  Reach
//
//  Created by Ismael Medina on 3/6/26.
//
import Foundation

//struct represents TaskItem meaning one task on the today tasks screen
//id uniquely identifies each task
//-1 is just a default placeholder id until a real backend id is used
//title is the task text for each taskitem
//isCompleted is used to check whether a checkmark has been checked or not (True ? False)
// Rrepresentation of a task on the Daily Goal Digest
struct TaskItem: Identifiable {
    var id: Int = -1
    let title: String
    var isCompleted: Bool
    
    //function builds dictionary that gets sent to the backend
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

