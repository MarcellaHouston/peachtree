//
//  GoalItem.swift
//  Reach
//
//  Created by Marcella Houston on 3/17/26.
//

import Foundation

struct GoalItem {
    struct RepeatDays {
        var sun: Bool = false
        var mon: Bool = false
        var tue: Bool = false
        var wed: Bool = false
        var thu: Bool = false
        var fri: Bool = false
        var sat: Bool = false
    }
    enum Difficulty {
        case easy
        case average
        case hard
    }
    
    var id: Int = -1
    var title: String = ""
    var category: String? = nil
    var difficulty: Difficulty = .average
    var repeatDays: RepeatDays = RepeatDays()
    var due: Date? = nil
    var isPaused: Bool = false
    
    // Return a dictionary in the format the backend wants to read
    func requestBody() -> [String:Any] {
        var body: [String:[String:Any]] = [
            "goal": [
                "name": title,
                // No description on frontend
                "measurable": "completion",// No measurable on frontend
                // No start_date on frontend
                "end_date": "2999-01-01",// end_date optional on frontend
                "user": "Reach staff"// TODO: Unhardcode the user
                
                // No difficulty on backend
                // No category (optional) on backend
                // No isPaused on backend
                // No repeat days on backend
            ]
        ]
        
        if id != -1 {
            body["goal"]!["id"] = id
        }
        
        // If we have an assigned due date, convert to string and send
        if let due = due {
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy-MM-dd"
            body["goal"]!["end_date"] = formatter.string(from: due)
        }
        
        return body
    }
}

// More readable and friendly way to declare a GoalItem instance
// GoalItemBuilder().title("example").build()
final class GoalItemBuilder {
    private(set) var goal = GoalItem()
    
    func build() -> GoalItem {
        return goal
    }
    
    // These functions modify goal and return self (of type Self aka GoalItemBuilder)
    // Return self so we can string member functions together
    func title(_ title: String) -> Self {
        goal.title = title
        return self
    }
    func category(_ cat: String) -> Self {
        goal.category = cat
        return self
    }
    func id(_ id: Int) -> Self {
        goal.id = id
        return self
    }
    func difficulty(_ dif: GoalItem.Difficulty) -> Self {
        goal.difficulty = dif
        return self
    }
    func due(_ due: Date) -> Self {
        goal.due = due
        return self
    }
    func pause() -> Self {
        goal.isPaused = true
        return self
    }
    // These set it to repeat on a specific day of the week
    func mon() -> Self {
        goal.repeatDays.mon = true
        return self
    }
    func tue() -> Self {
        goal.repeatDays.tue = true
        return self
    }
    func wed() -> Self {
        goal.repeatDays.wed = true
        return self
    }
    func thu() -> Self {
        goal.repeatDays.thu = true
        return self
    }
    func fri() -> Self {
        goal.repeatDays.fri = true
        return self
    }
    func sat() -> Self {
        goal.repeatDays.sat = true
        return self
    }
    func sun() -> Self {
        goal.repeatDays.sun = true
        return self
    }
}
