//
//  GoogleNavigationService.swift
//  Frontend
//

import Foundation
import UIKit
import CoreLocation


struct Command: Codable {
    let action: String
    let value: String? // optional in case some actions don't need values
}

@MainActor
class GoogleNavigationService {
    
    static let shared = GoogleNavigationService()
    
    private init() {}

    func handle(command: Command) {
            switch command.action {
            case "open":
                openGoogleMaps()
            case "close":
                closeGoogleMaps()
            case "setRoute":
                if let location = command.value {
                    setRoute(to: location)
                }
            // Add more cases here as needed
            default:
                print("Unknown command: \(command.action)")
            }
        }
    
    // MARK: - Open Google Maps app
    func openGoogleMaps() {
        guard let url = URL(string: "comgooglemaps://") else { return }
        if UIApplication.shared.canOpenURL(url) {
            UIApplication.shared.open(url)
        } else {
            print("Google Maps app is not installed.")
        }
    }

    // MARK: - Close Google Maps (limited control on iOS)
    func closeGoogleMaps() {
        // iOS does not allow force closing another app.
        // You can return the user to your app via a custom URL scheme if Google Maps opened your app that way.
        print("Closing not supported directly. Consider UI guidance to return.")
    }

    // MARK: - Set route to a location
    func setRoute(to destination: String) {
        let encoded = destination.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? ""
        if let url = URL(string: "comgooglemaps://?daddr=\(encoded)&directionsmode=driving") {
            UIApplication.shared.open(url)
        }
    }

    // MARK: - Add a stop (via waypoints)
    func addStop(currentDestination: String, waypoint: String) {
        let destEncoded = currentDestination.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? ""
        let waypointEncoded = waypoint.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? ""
        if let url = URL(string: "comgooglemaps://?daddr=\(waypointEncoded)+to:\(destEncoded)&directionsmode=driving") {
            UIApplication.shared.open(url)
        }
    }

    // MARK: - End route
    func endRoute() {
        // Not possible to programmatically end route in Google Maps once launched.
        // Optional: Open the app home again or alert the user.
        openGoogleMaps() // just brings user to the home view
    }
}
