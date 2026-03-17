//
//  GoalItem.swift
//  Reach
//
//  Created by Marcella Houston on 3/17/26.
//

import Foundation

struct GoalItem {
    struct RepeatDays {
        var sun: Bool
        var mon: Bool
        var tue: Bool
        var wed: Bool
        var thu: Bool
        var fri: Bool
        var sat: Bool
    }
    enum Difficulty {
        case easy
        case average
        case hard
    }
    
    var title: String
    var category: String
    var difficulty: Difficulty
    var repeatDays: RepeatDays
    var due: Date
}
