import SwiftUI

struct GoalsView: View {
    @Binding var selectedTab: AppTab

    var body: some View {
        VStack(spacing: 0) {
            VStack {
                Spacer()

                Text("Goals Screen")
                    .font(.largeTitle)
                    .foregroundColor(.white)

                Spacer()
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Color.black)

            BottomNavView(selectedTab: $selectedTab)
        }
        .background(Color.black)
        .ignoresSafeArea(edges: .bottom)
    }
}
