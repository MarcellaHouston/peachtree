//
//  ExampleView.swift
//  Reach
//
//  Created by Marcella Houston on 3/17/26.
//

// UM EECS Reactive

import SwiftUI

@Observable
final class RefCounter {
    var count = 0
}

@Observable
final class Words {
    var words = [String]()
}

struct ChildView: View {
    @Binding var count: Int
    
    var body: some View {
        Button("+1") { count += 1 }
    }
}

struct ChildView2: View {
    @Binding var words: [String]
    var body: some View {
        Button("Add word") { words.append("wow!") }
    }
}

struct ExampleContentView: View {
    let counter = RefCounter()
    let words = Words()
    
    var body: some View {
        @Bindable var bindable = counter
        @Bindable var bindable2 = words

        VStack {
            Text("\(counter.count)")
            Text(words.words.joined(separator: " "))
            ChildView(count: $bindable.count)
            ChildView2(words: Bindable(words).words)
        }
        .font(.system(size: 28))
    }
}

#Preview {
    ExampleContentView()
}
