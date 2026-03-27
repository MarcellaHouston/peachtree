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
    let id: Int
    let name: String
    let description: String?
    let measurable: String
    let start_date: String
    let end_date: String
    let user_id: String
    let active_date: String
    let difficulty: String
    let category: String?
    let days_of_week: String
    let isPaused: Bool
    
    func goal() -> GoalItem {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"

        var res = GoalItemBuilder().title(name).id(id)
        if end_date != NO_DUE {
            if let date = formatter.date(from: end_date) {
                res = res.due(date)
            }
        }
        if let cat = category {
            if cat != NO_CATEGORY {
                res = res.category(cat)
            }
        }
        if difficulty == "average" {
            res = res.difficulty(GoalItem.Difficulty.average)
        } else if difficulty == "hard" {
            res = res.difficulty(GoalItem.Difficulty.hard)
        } else {
            res = res.difficulty(GoalItem.Difficulty.easy)
        }
        
        if days_of_week.contains("sun") {
            res = res.sun()
        }
        if days_of_week.contains("mon") {
            res = res.mon()
        }
        if days_of_week.contains("tue") {
            res = res.tue()
        }
        if days_of_week.contains("wed") {
            res = res.wed()
        }
        if days_of_week.contains("thu") {
            res = res.thu()
        }
        if days_of_week.contains("fri") {
            res = res.fri()
        }
        if days_of_week.contains("sat") {
            res = res.sat()
        }
        
        return res.build()
    }
}
