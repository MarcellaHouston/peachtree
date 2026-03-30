//
//  PurpleButtonStyle.swift
//  Reach
//
//  Created by Marcella Houston on 3/27/26.
//

import SwiftUI

// A uniform button style
struct PurpleButtonStyle: ButtonStyle {
    let active: Bool

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .padding(.horizontal, 10)
            .padding(.vertical, 2)
            .background(active ? Color(red: 0.77, green: 0.69, blue: 0.94) : .white)
            .clipShape(.capsule)
            .frame(minWidth: 24, minHeight: 24)
            .overlay{
                if !active{
                    RoundedRectangle(cornerRadius: 10)
                        .stroke(.gray, lineWidth: 0.6)
                }
            }
    }
}
