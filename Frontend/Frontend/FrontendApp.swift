//
//  FrontendApp.swift
//  Frontend
//
//  Created by Gabriel Haskell on 7/10/25.
//

import SwiftUI

@main
struct FrontendApp: App {
    
    @StateObject private var smartLocationManager = SmartLocationManager()
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    @StateObject var sessionManager = SessionManager()

    
    var body: some Scene {
        WindowGroup {
            StartView(smartLocationManager: smartLocationManager)
                .environmentObject(sessionManager)
                .environmentObject(smartLocationManager)
        }
    }
}
