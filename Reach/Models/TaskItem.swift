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
struct TaskItem: Identifiable {
    //let id = UUID()
    var id: Int = -1
    let title: String
    var isCompleted: Bool
    
    //function builds dictionary that gets sent to the backend
    func requestBody() -> [String:Any] {
        let body: [String:[String:Any]] = [
            "task": [
                "name": title,
                "id": id,
                // No description in frontend
                "measurable": "completion",// No measurable in frontend
                // No start date in frontend
                "end_date": "2999-01-01",// No end date in frontend
                "user": "Reach Staff"// TODO: Unhardcode the user
                
                // No isCompleted in backend
            ]
        ]
        
        return body
    }
}

