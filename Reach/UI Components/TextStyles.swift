//
//  TextStyles.swift
//  Reach
//
//  Created by Marcella Houston on 3/27/26.
//

import SwiftUI

extension Text {
    func SmallHeader() -> Self {
        self.bold()
    }
    func BigHeader() -> Self {
        self.font(.system(size: 32, weight: .regular))
    }
}
