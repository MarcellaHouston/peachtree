//
//  UserCreds.swift
//  Reach
//
//  Created by Marcella Houston on 4/10/26.
//

// Manage persistant storage of user credentials (token, stringid, intid)

import Foundation
import Security
import SwiftUI

final class UserCreds {
    // Singleton stuff
    private init() {}
    static var shared = UserCreds()
    
    // Local copies so we don't have to accesss disk every time
    private var intId: Int? = nil
    private var stringId: String? = nil
    private var token: String? = nil
    
    
    // Load stored persistant data into intId, stringId, and token
    // Reset all to nil on failure
    private func getStored() {
        if let str = UserIdManager.getString(), let tok = TokenManager.get() {
            intId = UserIdManager.getInt()
            stringId = str
            token = tok
        }
        intId = nil
        stringId = nil
        token = nil
    }
    
    // Accessors
    func getIntId() -> Int? {
        if intId == nil {
            getStored()
        }
        return intId
    }
    func getStringId() -> String? {
        if stringId == nil {
            getStored()
        }
        return stringId
    }
    func getToken() -> String? {
        if token == nil {
            getStored()
        }
        return token
    }
    
    // Mutators
    // Return false if failed to set
    func set(string: String, int: Int, token tok: String) -> Bool {
        UserIdManager.set(string: string, int: int)
        if !TokenManager.save(token: tok) {
            UserIdManager.delete()
            intId = nil
            stringId = nil
            token = nil
            return false
        }
        intId = int
        stringId = string
        token = tok
        return true
    }
    func delete() -> Bool {
        intId = nil
        stringId = nil
        token = nil
        let res = TokenManager.delete()
        UserIdManager.delete()
        return res
    }
}

// Handle the persistant storage of user_id (string) and user_id (integer)
// Two because of legacy backend code?
private struct UserIdManager {
    // Make initializer private because only static functions
    private init() {}
    
    static private let STRING_KEY = "reach_app_user_id_string"
    static private let INT_KEY = "reach_app_user_id_integer"
    
    static func set(string: String, int: Int) {
        UserDefaults.standard.set(string, forKey: STRING_KEY)
        UserDefaults.standard.set(int, forKey: INT_KEY)
    }
    
    static func getInt() -> Int {
        return UserDefaults.standard.integer(forKey: INT_KEY)
    }
    
    static func getString() -> String? {
        return UserDefaults.standard.string(forKey: STRING_KEY)
    }
    
    static func delete() {
        UserDefaults.standard.removeObject(forKey: INT_KEY)
        UserDefaults.standard.removeObject(forKey: STRING_KEY)
    }
    
}

// Securely store, retrieve, and delete auth token to/fro the keychain
private struct TokenManager {
    // Make initializer private because only static functions
    private init() {}
    
    static private let service = "team_peachtree_reach_app"
    static private let account = "team_peachtree_reach_account"

    // Return nil on failure
    static func get() -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: account,
            kSecAttrService as String: service,
            // Request the data be returned
            kSecReturnData as String: true,
            // Only return one item (the first match)
            kSecMatchLimit as String: kSecMatchLimitOne
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        if status != errSecSuccess {
            return nil
        }
        
        // Turn result (AnyObject?) -> Data -> String
        if let resData = result as? Data {
            return String(data: resData, encoding: .utf8)
        }

        // Could not turn result into data
        return nil
    }
    
    // Return true on success, false on failure
    static func save(token: String) -> Bool {
        // Assert there's nothing already there
        if !delete(){
            return false
        }
        
        // Turn string (token) -> data
        guard let data = token.data(using: .utf8) else {
            return false
        }

        let query: [String: Any] = [
            // Define security class. This one is secure but very available, good for tokens
            kSecClass as String: kSecClassGenericPassword,
            
            // Give the token and specify where it goes
            kSecAttrAccount as String: account,
            kSecAttrService as String: service,
            kSecValueData as String: data
        ]
        
        // Actually store the info in the keychain
        let status = SecItemAdd(query as CFDictionary, nil)
        if status != errSecSuccess {
            return false
        }
        
        return true
    }
    
    // Return true on success, false on failure
    static func delete() -> Bool {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: account,
            kSecAttrService as String: service
        ]

        let status = SecItemDelete(query as CFDictionary)
        if status != errSecSuccess && status != errSecItemNotFound {
            return false
        }
        
        // Item got deleted or was already deleted, yay
        return true
    }
}

// Small cute demo of using the token
// Toying with it will affect the persistant data
#Preview {
    @Previewable @State var displayString: String = "Nothing retreived yet"
    @Previewable @State var status = false
    
    
    if !status {
        Text(displayString).foregroundColor(.red)
    } else {
        Text(displayString).foregroundColor(.green)
    }
    
    Button("save \"STAFF_USER_ID\", 1337, \"thistoken\"") {
        status = UserCreds.shared.set(string: STAFF_USER_ID, int: 1337, token: "thistoken")
    }
    Button("get token") {
        if let res = UserCreds.shared.getToken() {
            displayString = res
            status = true
        } else {
            status = false
            displayString = "failed to get token"
        }
    }
    Button("get string") {
        if let res = UserCreds.shared.getStringId() {
            displayString = res
            status = true
        } else {
            status = false
            displayString = "failed to get string"
        }
    }
    Button("get int") {
        if let res = UserCreds.shared.getIntId() {
            displayString = String(res)
            status = true
        } else {
            status = false
            displayString = "failed to get int"
        }
    }
    Button("delete") {
        status = UserCreds.shared.delete()
    }
}
