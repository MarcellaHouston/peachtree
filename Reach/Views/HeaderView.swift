//
//  HeaderView.swift
//  Reach
//
//  Created by Ismael Medina on 3/6/26.
//

import SwiftUI

//this view builds the top header for the today’s tasks screen
//it includes a small status bar row and a second row for the peach icon and account section
//the goal is to match the figma layout while keeping the structure simple
struct HeaderView: View {
    @Binding var isDemoMode: Bool
    @Binding var showSignIn: Bool
    @Binding var showDemoPopup: Bool
    @Binding var selectedTab: AppTab
    var showLeaveDemo: Bool
    var body: some View {
        VStack(spacing: 0) {
           
            HStack {
                //commented out because simulator already has the status bar
                
                /*
                Text("9:41")
                .font(.system(size: 17, weight: .semibold))
                .foregroundColor(.white)

                Spacer()

                HStack(spacing: 7) {
                    Image(systemName: "cellularbars")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(.white)

                    Image(systemName: "wifi")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(.white)

                    Image(systemName: "battery.100")
                    .font(.system(size: 20, weight: .regular))
                    .foregroundColor(.white)
                }
                 */
            }
             
            //this top row acts like a custom phone status bar
            //the horizontal padding keeps the time and icons from touching the edges
            //the small top padding moves the row close to the top like the design
            //.padding(.horizontal, 24)
            .padding(.horizontal, 24)
            .padding(.top, 8)

            HStack(spacing: 0) {
                HStack {
                    if showLeaveDemo {
                        Button("Leave Demo") {
                            isDemoMode = false
                            showDemoPopup = false
                            selectedTab = .todayTasks
                            showSignIn = true
                        }
                        .font(.system(size: 13, weight: .regular))
                        .foregroundColor(Color(red: 0.90, green: 0.34, blue: 0.31))
                    }
                }
                .frame(width: 86, alignment: .leading)

                Spacer()

                Circle()
                    .fill(Color(red: 0.89, green: 0.58, blue: 0.59))
                    .frame(width: 50, height: 50)

                Spacer()

                VStack(spacing: 3) {
                    Circle()
                        .fill(Color(red: 0.88, green: 0.83, blue: 0.97))
                        .frame(width: 34, height: 34)
                        .overlay {
                            Image(systemName: "person.crop.circle")
                                .font(.system(size: 18, weight: .regular))
                                .foregroundColor(Color(red: 0.34, green: 0.26, blue: 0.64))
                        }

                    Text("Account")
                        .font(.system(size: 9, weight: .semibold))
                        .foregroundColor(.white)
                }
                .frame(width: 86)
            }
            //this second row places the peach icon in the center area
            //the clear frame on the left and fixed frame on the right help keep the center icon visually centered
            //the account section is stacked so the icon sits above the label like the figma
            .padding(.horizontal, 18)
            .padding(.top, 14)
            
            //this spacer fills the remaining header height
            //it helps the header keep a consistent size without adding more visible content
            Spacer(minLength: 0)
        }
        //the fixed height keeps the header consistent across previews and the full screen
        //the black background matches the top section of the mockup
        .frame(height: 120)
        .background(Color.black)
    }
}

#Preview {
    HeaderView(isDemoMode: .constant(true), showSignIn: .constant(false), showDemoPopup: .constant(false), selectedTab: .constant(.todayTasks), showLeaveDemo: true)
}
