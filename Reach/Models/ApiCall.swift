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
    
    func refreshTasks() async {
        struct Res: Codable {
            let tasks: [TaskSchema]
        }
        let body: [String: Any] = [:]
        do {
            let res: Res = try await sendRequest("POST", body, "tasks")
            self.tasks = res.tasks.map() { x in x.buildTask() }
        } catch {
            print(error)
        }
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
        let decodedData = try JSONDecoder().decode(T.self, from: data)
        return decodedData
    }
}
