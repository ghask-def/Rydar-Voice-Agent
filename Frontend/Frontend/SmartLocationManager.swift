//
//  LocationOpener.swift
//  Frontend
//

import Foundation

import CoreLocation
import CoreMotion
import Combine

class SmartLocationManager: NSObject, ObservableObject, CLLocationManagerDelegate {
    private let manager = CLLocationManager()
    private let motionManager = CMMotionActivityManager()
    private var timer: Timer?

    @Published var currentCoordinates: [String]? = nil
    @Published var isTracking = false

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyBest
        manager.requestWhenInUseAuthorization()
    }

    // MARK: - Active Tracking (like Snap Map)
    func startActiveTracking(interval: TimeInterval = 15.0) {
        print("Starting active tracking")
        isTracking = true
        manager.desiredAccuracy = kCLLocationAccuracyBest
        manager.startUpdatingLocation()

        timer = Timer.scheduledTimer(withTimeInterval: interval, repeats: true) { [weak self] _ in
            self?.manager.requestLocation()
        }

        // Optional: Use motion to pause if stationary
        if CMMotionActivityManager.isActivityAvailable() {
            motionManager.startActivityUpdates(to: .main) { [weak self] activity in
                guard let self = self else { return }
                if activity?.stationary == true {
                    self.pauseTrackingDueToStationary()
                } else if self.isTracking == false {
                    self.resumeTrackingFromMotion()
                }
            }
        }
    }

    // MARK: - Passive Tracking (like background/ghost mode)
    func startPassiveTracking() {
        print("Starting passive low-power tracking")
        stopActiveTracking()
        
        DispatchQueue.main.async {
            self.isTracking = false
        }
        manager.startMonitoringSignificantLocationChanges()
    }

    func stopTrackingCompletely() {
        print("Stopping all location tracking")
        stopActiveTracking()
        manager.stopMonitoringSignificantLocationChanges()
        motionManager.stopActivityUpdates()
        isTracking = false
    }

    private func stopActiveTracking() {
        manager.stopUpdatingLocation()
        timer?.invalidate()
        timer = nil
    }

    private func pauseTrackingDueToStationary() {
        print("Paused tracking (user is stationary)")
        stopActiveTracking()
    }

    private func resumeTrackingFromMotion() {
        print("Resumed tracking (user is moving again)")
        startActiveTracking()
    }

    // MARK: - CLLocationManagerDelegate

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.last else { return }
        let lat = String(format: "%.6f", location.coordinate.latitude)
        let lng = String(format: "%.6f", location.coordinate.longitude)

        DispatchQueue.main.async {
            self.currentCoordinates = [lat, lng]
            print("Updated location: \(lat), \(lng)")
        }
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        print("Location error: \(error.localizedDescription)")
    }
}
