//
//  ConnectButtonView.swift
//  Frontend
//


// LiveKit server URL. Access tokens are fetched from the backend (/token/getToken).
let wsURL = "wss://YOUR-PROJECT.livekit.cloud"

@preconcurrency import LiveKit
import LiveKitComponents
import SwiftUI

struct ConnectButtonView: View {
    
    @EnvironmentObject var smartLocationManager: SmartLocationManager
    @StateObject var roomCtx: RoomContext
    
    init(smartLocationManager: SmartLocationManager) {
            _roomCtx = StateObject(wrappedValue: RoomContext(smartLocationManager: smartLocationManager))
        }
    
    var body: some View {
        VStack (spacing: 4) {
            VStack {
                if roomCtx.room.connectionState == .disconnected {
                    AnyView(
                        Button(action: {
                            Task {
                                await roomCtx.connectWithButton()
                            }
                        }) {
                            ZStack {
                                Circle()
                                    .foregroundColor(.white)
                                    .frame(height: 80)
                                Circle()
                                    .frame(height: 72)
                                    .foregroundColor(Color(red: 32/255, green: 58/255, blue: 250/255))

                                Image(systemName: "waveform")
                                    .foregroundColor(.white)
                                    .fontWeight(.bold)
                                    .padding()
                            }
                            .shadow(color: .black.opacity(0.25), radius: 5, x: 0, y: -5) // Shadow for whole stack
                        }
                    )
                } else {
                    AnyView(
                        Button(action: {
                            Task {
                                do {
                                    await roomCtx.room.disconnect()
                                }
                            }
                        }) {

                            ZStack {
                                Circle()
                                    .foregroundColor(.white)

                                    .frame(height: 80)
                                Circle()
                                    .frame(height: 72)
                                    .foregroundColor(Color(red: 32/255, green: 58/255, blue: 250/255))
                                
                                
                                if let track = roomCtx.room.agentParticipant?.audioTracks
                                    .first(where: { $0.source == .microphone })?.track as? AudioTrack {
                                                                        
                                    BarAudioVisualizer(audioTrack: track,
                                                       agentState: roomCtx.room.agentParticipant?.agentState ?? .listening,

                                                       barColor: .white,
                                                       barCount: 6,
                                                       barSpacingFactor: 0.1,
                                                       barMinOpacity: 0.2)
                                        .frame(width: 40, height: 40)
                                }
                                else {

                                    Image(systemName: "phone.down")
                                        .foregroundColor(.white)
                                        .fontWeight(.bold)
                                        .padding()
                                }

                            }
                            .shadow(color: .black.opacity(0.25), radius: 5, x: 0, y: -5) // Shadow for whole stack
                        }
                    )
                }
            }
            .padding()
            .environmentObject(roomCtx)
            .onAppear {
                Task {
                    try await roomCtx.connect()
                }
            }
        }
        
    }
}
