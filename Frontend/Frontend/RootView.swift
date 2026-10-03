import SwiftUI
import PostgREST
import FirebaseAuth
// !! Note !!


struct RootView: View {
    
    @EnvironmentObject var smartLocationManager: SmartLocationManager
    @StateObject var roomCtx: RoomContext
    @State var selectedTab: Tabs
    @State var selectedHomeTab: HomeTab = .services
    
    
    init(smartLocationManager: SmartLocationManager) {
            _roomCtx = StateObject(wrappedValue: RoomContext(smartLocationManager: smartLocationManager))
        selectedTab = .home
//        sendFirebaseUserIdToBackend()
        
        }
    
    var body: some View {
        ZStack {
            VStack {
                TopbarView(selectedTab: $selectedTab)
                Group {
                    switch selectedTab {
                    case .home:
                        HomeView(selectedHomeTab: $selectedHomeTab)
                    case .account:
                        AppIntegrationView()
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                CustomTabbarView(selectedTab: $selectedTab)
            }
            .ignoresSafeArea(edges: .bottom)
            VStack {
                Spacer()
                ConnectButtonView(smartLocationManager: smartLocationManager)
                    .padding(.bottom, 54)
            }
            .ignoresSafeArea()
        }
//        TabView {
        
    }
}


enum Tabs: Int {
    case home = 0
    case account = 1
}

struct CustomTabbarView: View {

    @Binding var selectedTab: Tabs

    var body: some View {
        ZStack {
            // Concave background with shadow
            ConcaveTabBarShape()
                .fill(Color.white)
                .shadow(color: .black.opacity(0.25), radius: 5, y: -5)
                .frame(height: 100) // OG 70
                .ignoresSafeArea()

            HStack {
                tabBarButton(image: "house", tab: .home, label: "Home")
                
                Text("Activate Rydar")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.top, 28)
                    // .frame(maxWidth: 80, maxHeight: .infinity)

                tabBarButton(image: "person", tab: .account, label: "Account")
            }
            .frame(height: 48)
            .padding(.bottom, 30)
        }
    }

    // Reusable tab bar button view
    func tabBarButton(image: String, tab: Tabs, label: String) -> some View {
        Button(action: {
            selectedTab = tab
        }) {
            VStack(spacing: 4) {
                Image(systemName: image)
                    .resizable()
                    .scaledToFit()
                    .frame(width: 24, height: 24)
                Text(label)
                    .font(.caption)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .foregroundColor(selectedTab == tab ? .primary : .secondary)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

struct ConcaveTabBarShape: Shape {
    func path(in rect: CGRect) -> Path {
        let radius: CGFloat = 42  // radius of the arc
        let smoothness: CGFloat = 10  // how round the corners are
        let centerX = rect.midX

        let arcStartX = centerX - radius
        let arcEndX = centerX + radius

        var path = Path()
        path.move(to: CGPoint(x: 0, y: 0))

        // Left straight edge
        path.addLine(to: CGPoint(x: arcStartX - smoothness, y: 0))

        // Left corner curve into arc
        path.addCurve(
            to: CGPoint(x: arcStartX, y: smoothness),
            control1: CGPoint(x: arcStartX - smoothness * 0.5, y: 0),
            control2: CGPoint(x: arcStartX, y: smoothness * 0.5)
        )

        // With this:
        path.addCurve(
            to: CGPoint(x: arcEndX, y: smoothness),
            control1: CGPoint(x: centerX - radius * 0.5, y: radius * 1.2),
            control2: CGPoint(x: centerX + radius * 0.5, y: radius * 1.2)
        )

        // Right corner curve out of arc
        path.addCurve(
            to: CGPoint(x: arcEndX + smoothness, y: 0),
            control1: CGPoint(x: arcEndX, y: smoothness * 0.5),
            control2: CGPoint(x: arcEndX + smoothness * 0.5, y: 0)
        )

        // Right straight edge and rest of tab bar
        path.addLine(to: CGPoint(x: rect.maxX, y: 0))
        path.addLine(to: CGPoint(x: rect.maxX, y: rect.maxY))
        path.addLine(to: CGPoint(x: 0, y: rect.maxY))
        path.closeSubpath()

        return path
    }
}

struct TopbarView: View {
    @Binding var selectedTab: Tabs

    var body: some View {
        VStack(spacing: 0) {
            ZStack {
                HStack {
                    // Rydar Logo
                    Text("Rydar")
                        .font(.system(size: 28, weight: .bold, design: .rounded))
                        .foregroundColor(Color(red: 32/255, green: 58/255, blue: 250/255))
                        .padding(.leading)
                    
                    Spacer()
                    
                    // Right-side buttons
                    HStack(spacing: 8) {
                        
                        if selectedTab == .home {
                            // Search button
                            Button(action: {
                                // Search action
                            }) {
                                Image(systemName: "plus")
                                    .font(.system(size: 18))
                                    .foregroundColor(.primary)
                                    .frame(width: 40, height: 40)
                                    .background(Color(.systemGray6))
                                    .clipShape(RoundedRectangle(cornerRadius: 16))
                            }
                        }
                        
                        // Notifications button
                        Button(action: {
                            // Notifications action
                        }) {
                            Image(systemName: "bell")
                                .font(.system(size: 18))
                                .foregroundColor(.primary)
                                .frame(width: 40, height: 40)
                                .background(Color(.systemGray6))
                                .clipShape(RoundedRectangle(cornerRadius: 16))
                        }
                        
                        // Premium button
                        Button(action: {
                            
                        }) {
                            Image(systemName: "sparkles")
                                .font(.system(size: 18))
                                .foregroundColor(.white)
                                .frame(width: 40, height: 40)
                                .background(
                                    LinearGradient(
                                        gradient: Gradient(colors: [
                                            Color.pink,
                                            Color(red: 32/255, green: 58/255, blue: 250/255)
                                        ]),
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                )
                                .clipShape(RoundedRectangle(cornerRadius: 16))
                        }
                    }
                    .padding(.trailing)
                }
            }
            .frame(height: 40)
            .background(Color(.systemBackground))
        }
    }
}
