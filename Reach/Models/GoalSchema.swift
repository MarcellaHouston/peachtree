//
//  GoalSchema.swift
//  Reach
//  Represents the exact schema used by the backend
//  Able to translate to schema used by frontend
//
//  Created by Marcella Houston on 3/23/26.
//

import Foundation

struct GoalSchema : Codable{
    let name: String
    let id: Int
    let description: String?
    let measurable: String
    let start_date: String
    let end_date: String
    let user: String
    
    func goal() -> GoalItem {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"

        var res = GoalItemBuilder().title(name)
        if let date = formatter.date(from: end_date) {
            return res.due(date).build()
        }
        return res.build()
    }
}
