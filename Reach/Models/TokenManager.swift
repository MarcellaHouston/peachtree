//
//  TokenManager.swift
//  Reach
//
//  Created by Marcella Houston on 4/7/26.
//

import Foundation
import Security
import SwiftUI

private let account = STAFF_USER_ID // TODO: Fix placeholder
private let service = "team_peachtree_reach_app"

// Securely store, retrieve, and delete auth token to/fro the keychain
struct TokenManager {
    // Make initializer private because only static functions
    private init() {}

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
    @Previewable @State var token = "No token retreived yet"
    @Previewable @State var status = false
    
    if !status {
        Text(token).foregroundColor(.red)
    } else {
        Text(token).foregroundColor(.green)
    }
    
    Button("save \"thistoken\"") {
        status = TokenManager.save(token: "thistoken")
    }
    Button("get") {
        if let res = TokenManager.get() {
            token = res
            status = true
        } else {
            status = false
            token = "failed to get token"
        }
    }
    Button("delete") {
        status = TokenManager.delete()
    }
}
