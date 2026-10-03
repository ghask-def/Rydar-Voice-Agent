//
//  MapsHelpers.swift
//  Frontend
//

import Foundation
import UIKit

func redirectToCurrentLocation(lat: Double, lon: Double) {
    let latitude = lat
    let longitude = lon

    let urlString = "https://www.google.com/maps/search/?api=1&query=\(latitude),\(longitude)"
    
    if let url = URL(string: urlString) {
        UIApplication.shared.open(url, options: [:], completionHandler: nil)
    }
}
