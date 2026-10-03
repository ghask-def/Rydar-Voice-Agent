import LiveKit
import FirebaseAuth
import SwiftUI
import Combine

@MainActor
final class RoomContext: ObservableObject {
    public let room = Room()
    @EnvironmentObject var sessionManager: SessionManager
    public var latestError: LiveKitError?
    let smartLocationManager: SmartLocationManager
    private var coordinateSubscriber: AnyCancellable?
    private var isAgentConnected = false
    @Published var connectionState: ConnectionState = .disconnected
    private var isRoomActive = false
    private var currentActiveRoom: Room? = nil
    

    var _connectTask: Task<Void, Error>?
    
    public init(smartLocationManager: SmartLocationManager) {
        self.smartLocationManager = smartLocationManager
        room.add(delegate: self)
        smartLocationManager.startPassiveTracking()
        
        // Note: We don't start location publishing here anymore
        // It will start when an agent participant connects
    }
    
    private func startLocationPublishing() {
        guard coordinateSubscriber == nil else {
            print("Location publishing already active")
            return
        }
        
        print("Starting location publishing to agent")
        coordinateSubscriber = smartLocationManager.$currentCoordinates
            .receive(on: DispatchQueue.main)
            .sink { [weak self] coords in
                guard let self = self, let coords = coords,
                      let lat = Double(coords[0]),
                      let lon = Double(coords[1]) else { return }

                print("Preparing to publish location: \(lat), \(lon)")
                
                let payload: [String: Any] = [
                    "type": "locationUpdate",
                    "latitude": lat,
                    "longitude": lon
                ]

                if let data = try? JSONSerialization.data(withJSONObject: payload) {
                    print("Location data serialized, sending in 2 seconds...")
                    Task {

                        do {
                            // Small delay to ensure agent backend is ready to receive data
                            try await Task.sleep(nanoseconds: 2_000_000_000) // 2 seconds
                            let options = DataPublishOptions(reliable: true)
                            try await self.room.localParticipant.publish(data: data, options: options)
                            print("Published location: \(lat), \(lon)")
                        } catch {
                            print("Failed to publish location: \(error)")
                        }
                    }
                }
            }
    }
    
    private func stopLocationPublishing() {
        print("Stopping location publishing")
        coordinateSubscriber?.cancel()
        coordinateSubscriber = nil
    }
    
    // Define a function to get a LiveKit token
    func fetchLiveKitToken(for roomName: String, userName: String) async throws -> String {
        // Build your URL (replace with your backend endpoint)
        guard let url = URL(string: "https://your-backend.com/getToken?roomName=\(roomName)&userName=\(userName)") else {
            throw URLError(.badURL)
        }
        
        // Perform the request
        let (data, _) = try await URLSession.shared.data(from: url)
        
        // Decode the token from JSON (assuming your backend returns { "token": "..." })
        struct TokenResponse: Codable {
            let token: String
        }
        
        let decoded = try JSONDecoder().decode(TokenResponse.self, from: data)
        return decoded.token
    }
    
    func connect() async throws -> Room {
        print("ROOM ACTIVITY: \(isRoomActive)")

        if let existingRoom = currentActiveRoom {
            return existingRoom
        }
        let tokenURL = URL(string: "http://localhost:8000/token/getToken")! // Replace with your actual backend URL

        var request = URLRequest(url: tokenURL)
        request.httpMethod = "GET"

        let (data, _) = try await URLSession.shared.data(for: request)

        struct TokenResponse: Decodable {
            let token: String
        }
        
        isRoomActive = true
        let tokenResponse = try JSONDecoder().decode(TokenResponse.self, from: data)
        
        let connectTask = Task.detached { [weak self] in
            guard let self else {return}
            try await self.room.connect(url: wsURL,
                                        token: tokenResponse.token,
                                        connectOptions: ConnectOptions(enableMicrophone: true)
            )
        }
        print("ROOM CONNECTION STATE: \(self.room.connectionState)")
        _connectTask = connectTask
        try await connectTask.value
        
        // updating participant attributes (from async function)
//        try await room.localParticipant.set(attributes: ["user_id" : Auth.auth().currentUser?.uid ?? "unknown"])
        try await room.localParticipant.set(attributes: ["userID" : Auth.auth().currentUser?.uid ?? "JohnDoe"])
        
        currentActiveRoom = room
        
        try await room.registerTextStreamHandler(for: "my-topic") { reader, participantIdentity in
            let info = reader.info

            print("""
                Text stream received from \(participantIdentity)
                Topic: \(info.topic)
                Timestamp: \(info.timestamp)
                ID: \(info.id)
                """)

            let text = try await reader.readAll()
            print("Received text: \(text)")

            // Try decoding JSON from text stream
            if let data = text.data(using: .utf8),
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let messageTopic = json["topic"] as? String,
               messageTopic == "going_to",
               let locationRaw = json["location"] as? String {

                print("Received 'going_to' destination (from stream): \(locationRaw)")

                let address = locationRaw.components(separatedBy: "—").last?.trimmingCharacters(in: .whitespacesAndNewlines) ?? locationRaw

                if let coords = await self.smartLocationManager.currentCoordinates,
                   let lat = Double(coords[0]),
                   let lon = Double(coords[1]) {

                    let origin = "\(lat),\(lon)"
                    let destinationEncoded = address.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? address
                    let urlStr = "https://www.google.com/maps/dir/?api=1&origin=\(origin)&destination=\(destinationEncoded)&travelmode=driving"

                    if let url = URL(string: urlStr) {
                        await UIApplication.shared.open(url, options: [:]) { success in
                            if success {
                                print("Opened Google Maps directions.")
                            } else {
                                print("Failed to open Google Maps.")
                            }
                        }
                    } else {
                        print("Invalid Google Maps URL.")
                    }

                } else {
                    print("Current coordinates unavailable.")
                }

            } else if text == "open_maps" {
                Task { @MainActor in
                    if let coords = self.smartLocationManager.currentCoordinates {
                        let latitude = Double(coords[0]) ?? 0
                        let longitude = Double(coords[1]) ?? 0
                        print("Latest coords: \(latitude), \(longitude)")
                        redirectToCurrentLocation(lat: latitude, lon: longitude)
                    } else {
                        print("No coordinates yet.")
                    }
                }
            } else {
                print("Unrecognized text stream content")
            }
        }

        return room
        
    }
    
    func connectWithButton() async {
        DispatchQueue.main.async { [weak self] in
            self?.connectionState = .connected
        }
        print("connecting audio")
        for participant in room.remoteParticipants.values {
            print("room part: \(participant.identity)")
        }
        do {
            try await room.localParticipant.setMicrophone(enabled: true)
            try await room.localParticipant.set(attributes:["userId" : Auth.auth().currentUser?.uid ?? "JohnDoe"])
        } catch {
            print("Failed to set microphone enabled: \(error)")
            // Handle error appropriately, e.g., show alert to user
        }
        do {
            guard let firstEntry = room.remoteParticipants.first else {
                print("No remote participants found")
                return
            }
            let firstIdentity = firstEntry.key
            print("First remote participant identity: \(firstIdentity)")

            let response = try await room.localParticipant.performRpc(
                destinationIdentity: firstIdentity,
                method: "greet",
                payload: "Hello from RPC!"
            )
            print("RPC response: \(response)")
        } catch let error as RpcError {
            print("RPC call failed: \(error)")
        } catch {
            print("Unexpected error: \(error)")
        }


    }
    
    func disconnect() async {
        await room.disconnect()
    }
    
    var isAgentActive: Bool {
        return isAgentConnected
    }
    
    deinit {
        // Can't call @MainActor methods from deinit, so we'll rely on the disconnect method
        // and the participant disconnect handler to clean up properly
        coordinateSubscriber?.cancel()
    }
}

extension RoomContext: RoomDelegate {
    
    nonisolated func room(_: Room, participantDidConnect participant: RemoteParticipant) {
        print("Remote participant joined: \(String(describing: participant.identity))")
        
        Task {
            do {
                try await room.localParticipant.setMicrophone(enabled: false)
                print("localParticipant microphone is not enabled")
            } catch {
                print("Failed to set microphone enabled: \(error)")
            }
        }

        // Print participant metadata (if any)
        print("Participant metadata: \(participant.metadata ?? "None")")

        // Print subscribed track types
        for pub in participant.trackPublications {
            print("\(pub.key) and \(pub.value)")
        }
        
        // Check if this is an agent participant (they typically have "agent" in their identity)
        if let identity = participant.identity, String(describing: identity).contains("agent") {
            Task { @MainActor in
                self.isAgentConnected = true
                self.startLocationPublishing()
            }
        }
        
//        DispatchQueue.main.async { [weak self] in
//                    self?.connectionState = .connected
//                }

        // Example: publish data when participant joins
        Task {
            let testData: [String: Any] = [
                "type": "agentJoined",
                "message": "Welcome agent \(String(describing: participant.identity))"
            ]

            if let jsonData = try? JSONSerialization.data(withJSONObject: testData) {
                let options = DataPublishOptions(reliable: true)
                do {
//                    try await Task.sleep(nanoseconds: 10_000_000_000)
                    try await room.localParticipant.publish(data: jsonData, options: options)
                    print("Sent welcome data to agent")
                } catch {
                    print("Failed to send data: \(error)")
                }
            }
        }
    }
    
    nonisolated func room(_: Room, participantDidDisconnect participant: RemoteParticipant) {
        print("Remote participant left: \(String(describing: participant.identity))")
        
        // Check if this was an agent participant
        if let identity = participant.identity, String(describing: identity).contains("agent") {
            Task { @MainActor in
                self.isAgentConnected = false
                self.stopLocationPublishing()
            }
        }
    }
    
    // receiving participant attributes changes
    nonisolated func room(_ room: Room, participant: Participant, didUpdateAttributes changedAttributes: [String: String]) {

    }

    // receiving room metadata changes
    nonisolated func room(_ room: Room, didUpdateMetadata newMetadata: String?) {

    }
}
