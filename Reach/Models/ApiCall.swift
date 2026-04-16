//
//  ApiCall.swift
//  Reach
//
//  Created by Marcella Houston on 3/22/26.
//

import SwiftUI

// Singleton design pattern
// This class is observable so you may put ApiCall.shared.<goals / tasks / ...>
// anywhere you need to observe a user's data on the backend
@Observable
final class ApiCall {
    static let shared = ApiCall()
    private init() {}

    // goal is being created
    private(set) var isCreatingGoal: Bool = false
    private let serverUrl = "http://34.192.65.138"
    
    private(set) var goals = [GoalItem]()
    private(set) var tasks = [TaskItem]()
    private(set) var goalMods = [GoalModification]()
    private(set) var weeklyRecapSuggestions = [[String: String]]()
    private(set) var selectedWeeklyRecapSuggestions = [Bool]()
    
    func toggleMod(ind: Int) {
        goalMods[ind].active.toggle()
    }
    
    func toggleWeeklyRecapSuggestion(ind: Int) {
        selectedWeeklyRecapSuggestions[ind].toggle()
    }
    
    //Added
    private(set) var taskGoalNames: [Int:String] = [:]
    // Goal id -> index in goals that id is at
    private(set) var idToGoalInd: [Int:Int] = [:]
    
    // Populate with fallback data
    func fallback() {
        goalMods = FallbackData.fallbackGoalMods
        goals = FallbackData.fallbackGoals
        tasks = FallbackData.fallbackTasks
        taskGoalNames = FallbackData.fallbackTaskGoalNames
    }
    func goalOf(id: Int) -> GoalItem {
        if let goalsInd = idToGoalInd[id], goals[goalsInd].id == id {
            return goals[goalsInd]
        }
        // Out of date map, refresh it
        idToGoalInd = [:]
        for i in 0..<goals.count {
            idToGoalInd[goals[i].id] = i
        }
        
        if let goalsInd = idToGoalInd[id] {
            return goals[goalsInd]
        }
        return GoalItemBuilder().title("Some Goal That Doesn't Exist").build()
    }
    
    // Sends call to update all goals that are denoted to update in goalMods
    func applyGoalMods() async {
        // Goal id -> new version of goal (has the mods)
        var modifyGoals: [Int:GoalItem] = [:]
        for goalMod in goalMods {
            // Check if we've seen this goal before
            if goalMod.id < 0 {
                continue
            }else if modifyGoals[goalMod.id] == nil {
                modifyGoals[goalMod.id] = goalOf(id: goalMod.id)
            }
            
            // Modify the goal
            modifyGoals[goalMod.id]?.modify(modification: goalMod)
        }
        
        // API call modify all goals
        for entry in modifyGoals {
            await updateGoal(goal: entry.value)
            if entry.value.isPaused {
                await snoozeGoal(goal: entry.value)
            }
        }
    }
    
    // Syncs local goals variable to database info
    func refreshGoals() async {
        // Wrapper struct because result is an object, not an array
        struct Res: Codable {
            let goals: [GoalSchema]
        }
<<<<<<< HEAD
=======
        // send username in body
>>>>>>> 693e356 (Changed refreshGoals to send username in request body)
        let body: [String: Any] = [
            "user_id": UserCreds.shared.getStringId() as Any
        ]
        do {
            let res: Res = try await sendRequest("POST", body, "goals")
            self.goals = res.goals.map() { x in x.goal() }
        } catch {
            print(error)
        }
    }
    
    // Syncs local tasks variable to database info
    func refreshTasks() async -> Bool{
        struct DailyDigestTask: Codable {
            let task_id: Int
            let task: String
            let goal_name: String
            //added
            let completed: Bool
        }
        
        struct Res: Codable {
            let day: String
            let tasks: [DailyDigestTask]
        }
        
        let body: [String: Any] = [
            "user_id": UserCreds.shared.getStringId() as Any
        ]
        
        do {
            //test backend
            let res: Res = try await sendRequest("POST", body, "daily_goal_digest")
            //test fallback
            //let res: Res = try await sendRequest("POST", body, "daily_goal_digest_broke")
            self.tasks = res.tasks.map {
                TaskItem(id: $0.task_id, title: $0.task, isCompleted: $0.completed)
            }
            
            self.taskGoalNames = [:]
            for task in res.tasks {
                self.taskGoalNames[task.task_id] = task.goal_name
            }
            //REMOVE ONLY FOR DEBUGGING
            //print("=== TASKS FROM BACKEND ===")
            //for task in self.tasks {
             //   print("ID: \(task.id), TITLE: \(task.title)")
           // }
          //  print("==========================")
            //REMOVE ONLY FOR DEBUGGING
            return true
        }catch {
            print(error)
            return false
        }
    }
    
    // This class exists so we can properly JSONify an empty return result
    private struct Empty: Codable {}
    
    // Informs backend of change and refreshes goals
    func updateGoal(goal: GoalItem) async {
        //goal id less than 0 means it hasn't been assigned one yet
        if goal.id < 0 {
            print("Modifying goal should not have dummy id")
            return
        }
        let body: [String: Any] = goal.requestBody()
        
        do {
            let _: Empty = try await sendRequest("POST", body, "goals/update")
        } catch {
            print("updateGoal ERROR:")
            print(error)
        }
        await refreshGoals()
    }
    func createGoal(goal: GoalItem) async -> Int? {
        self.isCreatingGoal = true
        var goal = goal
        // randomly assign a negative number to avoid duplicate -1 id's
        if goal.id == -1 {
            goal.id = -Int.random(in: 1...1_000_000)
        }
        let body: [String: Any] = goal.requestBody()
        
        //adding a goal locally so appears instantly
        self.goals.append(goal)
        
        //updating dictionary to handle index shifts
        self.idToGoalInd = [:]
        /*
        print("DEBUG: Created local goal with ID: \(goal.id)")
         */
        struct Res: Codable {
            let goal_id: Int
        }
        do {
            let res: Res = try await sendRequest("POST", body, "goals/create")
            self.isCreatingGoal = false
            await refreshGoals()
            return res.goal_id
            
        } catch {
            print("createGoal ERROR:")
            print(error)
            return nil
        }
    }
    
    func snoozeGoal(goal: GoalItem) async {
        //goal id less than 0 means it hasn't been assigned one yet
        if goal.id < 0 {
            print("Snoozing goal should not have dummy id")
            return
        }
        let body: [String:Any] = ["id": goal.id, "weeks": 1]
        
        do {
            let _: Empty = try await sendRequest("POST", body, "goals/snooze")
        } catch {
            print("snoozeGoal ERROR:")
            print(error)
        }
        await refreshGoals()
    }
    func deleteGoal(goal: GoalItem) async {
        //goal id less than 0 means it hasn't been assigned one yet
        if goal.id < 0 {
            print("Modifying goal should not have dummy id")
            return
        }
        let body: [String:Any] = ["id": goal.id]
        
        do {
            let _: Empty = try await sendRequest("POST", body, "goals/delete")
        } catch {
            print("deleteGoal ERROR:")
            print(error)
        }
        await refreshGoals()
    }
    
    // Informs backend of change and refreshes tasks
    func toggleTask(task: TaskItem) async {
        let body: [String:Any] = [
            "user_id": UserCreds.shared.getStringId() as Any,
            "task_id": task.id,
            "status": !task.isCompleted
        ]
        
        do {
            let _: Empty = try await sendRequest("POST", body, "tasks/complete")
        } catch {
            print("toggleTask ERROR:")
            print(error)
        }
        await refreshTasks()
    }
    
    func login(username: String, password: String, andRegister: Bool = false) async -> Bool {
        struct Res: Codable {
            let authorization: String
            let intID: Int
            let stringID: String
            
            enum CodingKeys: String, CodingKey {
                case authorization = "Authorization"
                case intID = "User-ID"
                case stringID = "user_id"
            }

        }
        
        let body: [String:Any] = [
            "username": username,
            "password": password
        ]
        
        do {
            let res: Res = try await sendRequest("POST", body, andRegister ? "signup" : "login")
            //print(res)
            return UserCreds.shared.set(string: res.stringID, int: res.intID, token: res.authorization)
        } catch {
            print("login ERROR:")
            print(error)
            return false
        }
    }
    
    // fetches the weekly recap from the backend using the logged in user's credentials
    // returns the summary string and the suggested changes in a ui-friendly format
    func fetchWeeklyRecap() async -> (weeklySummary: String, changesTitle: String, changesSummary: String, suggestions: [[String: String]], completed: Int, total: Int)? {
        struct SuggestedChange: Codable {
            let goal_id: Int
            let difficulty: String?
            let days_of_week: String?
            let name: String?
            let end_date: String?
            let summary: String
        }

        struct Res: Codable {
            struct Stats: Codable {
                let completed: Int
                let total: Int
            }

            let suggested_changes: [SuggestedChange]
            let weekly_summary: String
            let changes_title: String
            let changes_summary: String
            let stats: Stats
        }

        let body: [String: Any] = [
            "user_id": UserCreds.shared.getStringId() as Any
        ]

        do {
            let decoded: Res = try await sendRequest("POST", body, "weekly_recap")

            let suggestions = decoded.suggested_changes.map { change in
                var result: [String: String] = [
                    "goal_id": String(change.goal_id),
                    "summary": change.summary
                ]

                if let difficulty = change.difficulty {
                    result["difficulty"] = difficulty
                }
                if let days = change.days_of_week {
                    result["days_of_week"] = days
                }
                if let name = change.name {
                    result["name"] = name
                }
                if let endDate = change.end_date {
                    result["end_date"] = endDate
                }

                return result
            }
            self.weeklyRecapSuggestions = suggestions
            self.selectedWeeklyRecapSuggestions = Array(repeating: false, count: suggestions.count)

            return (weeklySummary: decoded.weekly_summary, changesTitle: decoded.changes_title, changesSummary: decoded.changes_summary, suggestions: suggestions,
                completed: decoded.stats.completed, total: decoded.stats.total)
            
        } catch {
            print("weekly_recap ERROR:")
            print(error)
            return nil
        }
    }
    
    
    func selectedRecapSuggestions() -> [[String: String]] {
        weeklyRecapSuggestions.enumerated().compactMap { index, suggestion in
            guard index < selectedWeeklyRecapSuggestions.count,
                  selectedWeeklyRecapSuggestions[index] else {
                return nil
            }
            return suggestion
        }
    }
    
    
    // sends the user's accepted weekly recap suggestions back to backend
    func receiveSuggestions(_ acceptedSuggestions: [[String: String]]) async -> Bool {
        let allowedKeys: Set<String> = ["goal_id", "name", "end_date", "difficulty", "days_of_week"]

        let cleanedChanges: [[String: Any]] = acceptedSuggestions.compactMap { suggestion in
            guard let goalIdString = suggestion["goal_id"], let goalId = Int(goalIdString) else {
                return nil
            }

            var cleaned: [String: Any] = ["goal_id": goalId]

            for key in allowedKeys {
                if key == "goal_id" {
                    continue
                }
                if let value = suggestion[key] {
                    cleaned[key] = value
                }
            }

            return cleaned
        }

        let body: [String: Any] = [
            "user_id": UserCreds.shared.getStringId() as Any,
            "changes": cleanedChanges
        ]

        do {
            let _: Empty = try await sendRequest("POST", body, "receive_suggestions")
            //weeklyRecapSuggestions = []
            //selectedWeeklyRecapSuggestions = []
            return true
        } catch {
            print("receive_suggestions ERROR:")
            print(error)
            return false
        }
    }
    
    
    // Abstracted function to send a request and return some Decodable struct as response
    private func sendRequest<T: Decodable>(_ method: String, _ body: [String: Any], _ endpoint: String) async throws -> T{
        //print(body)
        guard let url = URL(string: "\(serverUrl)/\(endpoint)") else {
            throw URLError(.badURL)
        }
        
        var request = URLRequest(url: url)
        request.timeoutInterval = 60  // 1 minute
        request.httpMethod = method
        request.setValue(
            "application/json; charset=utf-8",
            forHTTPHeaderField: "Content-Type"
        )
        
        // Auth
        request.setValue(
            UserCreds.shared.getToken(),
            forHTTPHeaderField: "Authorization"
        )
        request.setValue(
            String(UserCreds.shared.getIntId() ?? -1),
            forHTTPHeaderField: "User-ID"
        )
        
        
        request.setValue("application/*", forHTTPHeaderField: "Accept")
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        // print(request.allHTTPHeaderFields)
        
        // Actual request and async stuff
        let (data, response) = try await URLSession.shared.data(for: request)
        
        /*
        guard let response = response as? HTTPURLResponse, (200...299).contains(response.statusCode) else {
            throw URLError(.badServerResponse)
        }
         */
        guard let response = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        if !(200...299).contains(response.statusCode) {
            print("status code:", response.statusCode)
            print("response body:", String(data: data, encoding: .utf8) ?? "no response body")
            throw URLError(.badServerResponse)
        }
        
        //print(String(data: data, encoding: .utf8)!)
    
        // Check if the server returned no data and empty response type
        if data.isEmpty && T.self == Empty.self {
            
            // return a empty object instead of trying to decode bc it may crash
            return Empty() as! T
            
        }
     
        let decodedData = try JSONDecoder().decode(T.self, from: data)
        return decodedData
    }
}
