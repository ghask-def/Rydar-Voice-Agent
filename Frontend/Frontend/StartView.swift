//
//  StartView.swift
//  Frontend
//
//  Created by Gabriel Haskell on 7/22/25.
//
import SwiftUI

struct StartView: View {
    @EnvironmentObject var sessionManager: SessionManager
    @EnvironmentObject var smartLocationManager: SmartLocationManager
    @StateObject var roomCtx: RoomContext
    
    init(smartLocationManager: SmartLocationManager) {
            _roomCtx = StateObject(wrappedValue: RoomContext(smartLocationManager: smartLocationManager))
        }

    var body: some View {
        Group {
            if sessionManager.isSignedIn {
                RootView(smartLocationManager: smartLocationManager)
                    .environmentObject(smartLocationManager)
//                AppIntegrationView()
            } else {
                 SignInView()
            }
        }
        .onAppear {
            sessionManager.listenToAuthState()
        }
    }
}

