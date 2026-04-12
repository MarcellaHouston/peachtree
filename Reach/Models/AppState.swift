//
//  AppState.swift
//  Reach
//
//  Created by Ismael Medina on 4/7/26.
//

import Foundation

enum AuthScreen {
    case signIn
    case signUp
}

//this struct holds all global app-level state
//it is passed as a single binding instead of multiple individual bindings
struct AppState {
    //navigation
    var selectedTab: AppTab = .todayTasks
    
    //auth
    var showSignIn: Bool = true
    
    //demo mode state
    var isDemoMode: Bool = false
    var showDemoPopup: Bool = false
    
    var authScreen: AuthScreen = .signIn
}
