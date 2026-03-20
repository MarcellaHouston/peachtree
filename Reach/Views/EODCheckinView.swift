import SwiftUI

struct EODCheckinView: View {
    @Binding var selectedTab: AppTab

    var body: some View {
        VStack(spacing: 0) {
            VStack {
                Spacer()

                Text("End of Day Screen")
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
