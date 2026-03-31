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

    private let serverUrl = "http://34.192.65.138"
    
    private(set) var goals = [GoalItem]()
    private(set) var tasks = [TaskItem]()
    //Added
    private(set) var taskGoalNames: [Int:String] = [:]
    
    // Syncs local goals variable to database info
    func refreshGoals() async {
        // Wrapper struct because result is an object, not an array
        struct Res: Codable {
            let goals: [GoalSchema]
        }
        let body: [String: Any] = [:]
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
            "user_id": STAFF_USER_ID
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
        if goal.id == -1 {
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
    func createGoal(goal: GoalItem) async {
        let body: [String: Any] = goal.requestBody()
        // Backend will ignore goalid
        
        do {
            let _: Empty = try await sendRequest("POST", body, "goals/create")
        } catch {
            print("createGoal ERROR:")
            print(error)
        }
        await refreshGoals()
    }
    func snoozeGoal(goal: GoalItem) async {
        if goal.id == -1 {
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
        if goal.id == -1 {
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
            "user_id": STAFF_USER_ID,
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
    
    // Abstracted function to send a request and return some Decodable struct as response
    private func sendRequest<T: Decodable>(_ method: String, _ body: [String: Any], _ endpoint: String) async throws -> T{
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
        request.setValue("application/*", forHTTPHeaderField: "Accept")
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        // Actual request and async stuff
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let response = response as? HTTPURLResponse, (200...299).contains(response.statusCode) else {
            throw URLError(.badServerResponse)
        }
        
        //print(String(data: data, encoding: .utf8)!)
        // TODO: Fix inconsequential bug of trying to decode an Empty data
        let decodedData = try JSONDecoder().decode(T.self, from: data)
        return decodedData
    }
}
