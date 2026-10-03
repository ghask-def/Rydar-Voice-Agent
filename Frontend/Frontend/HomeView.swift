
import SwiftUI

struct HomeView: View {
//    @EnvironmentObject var smartLocationManager: SmartLocationManager
//    @StateObject var roomCtx: RoomContext
    @Binding var selectedHomeTab: HomeTab
    
    var body: some View {
        VStack {
            
            HomeTabbarView(selectedHomeTab: $selectedHomeTab)
            
            Group {
                switch selectedHomeTab {
                case .services:
                    ServicesView()
                case .history:
                    HistoryView()
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }
}

enum HomeTab: String {
    case services = "Services"
    case history = "History"
}

struct HomeTabbarView: View {
    @Binding var selectedHomeTab: HomeTab
    
    var body: some View {
        VStack(spacing: 0) {
            HStack (spacing: 0) {
                Button(action: {
                    selectedHomeTab = .services
                }) {
                    ListTabbarElementView(
                        title: "Services",
                        isSelected: selectedHomeTab == .services
                    )
                }
                .buttonStyle(.plain)

                Button(action: {
                    selectedHomeTab = .history
                }) {
                    ListTabbarElementView(
                        title: "History",
                        isSelected: selectedHomeTab == .history
                    )
                }
                .buttonStyle(.plain)
            }
            .padding(.top)

            Divider()
        }
    }
}

struct ListTabbarElementView: View {
    let title: String
    let isSelected: Bool
    
    var body: some View {
        VStack(spacing: 12) {
            Text(title)
                .font(.subheadline)
                .fontWeight(.medium)
                .foregroundColor(isSelected ? .primary : .secondary)
            
            if isSelected {
                Color(red: 32/255, green: 58/255, blue: 250/255)
                    .frame(height: 2)
            } else {
                Color.clear.frame(height: 2)
            }
        }
    }
}
