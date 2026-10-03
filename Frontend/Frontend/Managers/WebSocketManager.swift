//
//  WebsocketManager.swift
//  Frontend
//

import Foundation

class WebSocketManager: ObservableObject {
    private var webSocketTask: URLSessionWebSocketTask?
    private let url = URL(string: "ws://192.168.1.18:8000/ws")! // Replace with your backend IP
    private var isConnected = false

    @Published var lastMessage: String = "-- none yet --"

    func connect() {
        guard !isConnected else {
            print("Already connected — skipping connect()")
            return
        }

        print("Connecting to WebSocket...")
        webSocketTask = URLSession.shared.webSocketTask(with: url)
        webSocketTask?.resume()
        isConnected = true

        listen()
        sendHandshake()

        DispatchQueue.main.asyncAfter(deadline: .now() + 10) {
            print("Still connected after 10 seconds")
        }
    }

    func disconnect() {
        print("Disconnecting WebSocket...")
        isConnected = false
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        webSocketTask = nil
    }

    func sendHandshake() {
        let message = URLSessionWebSocketTask.Message.string("handshake:ready")
        webSocketTask?.send(message) { error in
            if let error = error {
                print("Failed to send handshake: \(error)")
            } else {
                print("Handshake sent")
            }
        }
    }

    private func listen() {
        guard let task = webSocketTask else {
            print("Tried to listen with nil WebSocketTask")
            return
        }

        task.receive { [weak self] result in
            guard let self = self else { return }

            switch result {
            case .failure(let error):
                print("WebSocket error: \(error)")
                self.isConnected = false
                self.webSocketTask = nil
                return // stop listening after failure

            case .success(let message):
                switch message {
                case .string(let text):
                    DispatchQueue.main.async {
                        print("Received from backend:", text)
                        self.lastMessage = text
                    }
                default:
                    print("Received non-text WebSocket message")
                }

                self.listen() // keep listening on success
            }
        }
    }

    @MainActor
    func handleCommand(_ commandJSON: String) {
        guard let data = commandJSON.data(using: .utf8) else { return }
        if let command = try? JSONDecoder().decode(Command.self, from: data) {
            GoogleNavigationService.shared.handle(command: command)
        }
    }

    deinit {
        print("WebSocketManager deinitialized")
        disconnect()
    }
}
