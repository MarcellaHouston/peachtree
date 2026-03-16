//
//  BottomNavView.swift
//  Reach
//
//  Created by Ismael Medina on 3/6/26.
//

import SwiftUI

//this view builds the bottom navigation area for the today’s tasks screen
//right now only the today’s tasks tab is active, while the other tabs are shown
//so the screen matches the full app layout from the design
struct BottomNavView: View {
    var body: some View {
        HStack(spacing: 0) {
            navItem(title: "Today’s Tasks", selected: true, systemImage: "star.circle.fill")
            navItem(title: "Goals", selected: false, systemImage: "star.circle")
            navItem(title: "Weekly Recap", selected: false, systemImage: "star.circle")
            navItem(title: "End of Day", selected: false, systemImage: "star.circle")
        }
        //these paddings give the bar spacing similar to the figma design
        //the fixed height keeps the navigation bar size consistent at the bottom
        .padding(.horizontal, 10)
        .padding(.top, 10)
        .padding(.bottom, 14)
        .frame(height: 102)
        .background(Color.black)
    }

    //this helper creates one navigation item
    //each item uses the same structure so the code stays cleaner and easier to update
    //the selected item uses a filled icon and a light purple capsule background
    //the unselected items stay white and do not show the capsule
    private func navItem(title: String, selected: Bool, systemImage: String) -> some View {
        VStack(spacing: 8) {
            Image(systemName: systemImage)
            //the icon changes color depending on whether the tab is selected
            //the frame gives each icon the same tappable area and visual size
            .font(.system(size: 22, weight: .medium))
            .foregroundColor(selected ? Color(red: 0.29, green: 0.22, blue: 0.55): .white)
            .frame(width: 62, height: 36)
            .background(selected ? Color(red: 0.88, green: 0.83, blue: 0.97) : Color.clear)
            .clipShape(Capsule())

            Text(title)
            //the text is kept small so all four labels fit on one row
            //minimumScaleFactor helps prevent the longer labels from getting cut off too early
            .font(.system(size: 11, weight: .semibold))
            .foregroundColor(.white)
            .lineLimit(1)
            .minimumScaleFactor(0.72)
        }
        //this makes each tab take up equal width across the whole navigation bar
        .frame(maxWidth: .infinity)
    }
}

#Preview {
    VStack(spacing: 0) {
        Spacer()
        BottomNavView()
    }
    .background(Color.black)
}
