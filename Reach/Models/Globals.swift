//
//  Globals.swift
//  Reach
//
//  Created by Marcella Houston on 3/27/26.
//

// Special values representing a lack of goal information
// TODO: Replace these with optionals in backend database
import SwiftUI

let NO_CATEGORY = "EMPTY_CATEGORY"
let NO_DUE = "2999-01-01"

let STAFF_USER_ID = "Reach staff"

@Observable
final class AppState {
    //shared is a single global instance of AppState used across the entire app
    static let shared = AppState()
    //init is a private so no other instances can be created that enforces one shared state
    private init() {}

    var selectedTab: AppTab = .todayTasks

    //auth
    var showSignIn: Bool = true

    //demo mode state
    var isDemoMode: Bool = false
    var showDemoPopup: Bool = false

    //account popup state
    var showSignOutPopup: Bool = false
}
