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
        
        func toString() -> String {
            var res: [String] = []
            if sun {
                res.append("sunday")
            }
            if mon {
                res.append("monday")
            }
            if tue {
                res.append("tuesday")
            }
            if wed {
                res.append("wednesday")
            }
            if thu {
                res.append("thursday")
            }
            if fri {
                res.append("friday")
            }
            if sat {
                res.append("saturday")
            }
            return res.joined(separator: ",")
        }
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
                "measurable": "completion",
                "end_date": NO_DUE,
                "category": NO_CATEGORY,
                "user_id": UserCreds.shared.getStringId() as Any,
                "difficulty": "easy",
                "days_of_week": repeatDays.toString()
            ]
        ]
        
        if difficulty == .average {
            body["goal"]!["difficulty"] = "average"
        } else if difficulty == .hard {
            body["goal"]!["difficulty"] = "hard"
        }
        if let cat = category {
            body["goal"]!["category"] = cat
        }
        
        if id >= 0 {
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
    
    mutating func modify(modification mod: GoalModification) {
        if mod.key == .title {
            title = mod.val
        } else if mod.key == .category {
            if mod.val != ""{
                category = mod.val
            } else {
                category = nil
            }
        } else if mod.key == .difficulty {
            if mod.val == "average" {
                difficulty = .average
            } else if mod.val == "hard" {
                difficulty = .hard
            } else {
                difficulty = .easy
            }
        } else if mod.key == .repeatDays {
            let daysString = mod.val.lowercased()
            repeatDays.sun = daysString.contains("sun")
            repeatDays.mon = daysString.contains("mon")
            repeatDays.tue = daysString.contains("tue")
            repeatDays.wed = daysString.contains("wed")
            repeatDays.thu = daysString.contains("thu")
            repeatDays.fri = daysString.contains("fri")
            repeatDays.sat = daysString.contains("sat")
        } else if mod.key == .due {
            if mod.val != NO_DUE {
                let formatter = DateFormatter()
                formatter.dateFormat = "yyyy-MM-dd"
                if let date = formatter.date(from: mod.val) {
                    due = date
                }
            } else {
                due = nil
            }
        } else if mod.key == .pauseState {
            if mod.val == "true" {
                isPaused = true
            } else if mod.val == "false" {
                isPaused = false
            }
        }
    }
}

struct GoalModification {
    enum Key {
        case title
        case category
        case difficulty
        case repeatDays
        case due
        case pauseState
    }
    
    let id: Int
    let key: Key
    let val: String
    var active: Bool = true
    
    func toString() -> String {
        if key == .title {
            return "Set title to " + val
        } else if key == .category {
            if val != "" {
                return "Set category to " + val
            } else {
                return "Remove category"
            }
        } else if key == .difficulty {
            return "Set difficulty to " + val
        } else if key == .repeatDays {
            return "Set repeat days to " + val
        } else if key == .due {
            if val != NO_DUE {
                return "Set end date to " + val
            } else {
                return "Remove end date"
            }
        }
        return "Set paused to " + val
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
