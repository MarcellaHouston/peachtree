//
//  ConfirmPopup.swift
//  Reach
//
//  Created by Marcella Houston on 3/27/26.
//

import SwiftUI

// Reusable view for any kind of confirmation popup
// Automatically closes self upon hitting cancel or confirm
struct ConfirmPopup: View {
    @Binding var isShown: Bool // Pass a variable like '$showingPopup' to bind
    
    let prompt: String
    let desc: String
    
    let confirm: String
    let effect: () -> Void
    
    var body: some View {
        VStack(spacing: 0) {
            Text(prompt).BigHeader()
            Text(desc)
            HStack{
                Button("Cancel") {
                    isShown = false
                }
                .buttonStyle(PurpleButtonStyle(active: false))
                Button(confirm) {
                    effect()
                    isShown = false
                }
                .buttonStyle(PurpleButtonStyle(active: true))
            }
        }
        .frame(width: 310)
        .background(.white)
        .cornerRadius(15)
    }
}
