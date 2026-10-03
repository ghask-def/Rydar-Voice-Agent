import SwiftUI

struct AppIntegrationView: View {
    @StateObject private var oauthManager = GmailOAuthManager()
    @EnvironmentObject var session: SessionManager

    @State private var showDisconnectConfirmation = false

    var body: some View {
        VStack(spacing: 20) {
            Text("Gmail Integration")
                .font(.title)

            if session.isGmailConnected {
                Button("Disconnect Gmail") {
                    showDisconnectConfirmation = true
                }
                .foregroundColor(.red)
                .confirmationDialog(
                    "Are you sure you want to disconnect Gmail?",
                    isPresented: $showDisconnectConfirmation,
                    titleVisibility: .visible
                ) {
                    Button("Disconnect", role: .destructive) {
                        disconnectGmail()
                    }

                    Button("Cancel", role: .cancel) { }
                }
            } else {
                Button("Connect Gmail") {
                    oauthManager.startOAuthFlow()
                }
            }

            if oauthManager.isSignedIn {
                Text("Signed in as: \(oauthManager.userEmail)")
                    .font(.subheadline)
                    .foregroundColor(.gray)
            }
        }
        .padding()
    }

    private func disconnectGmail() {
        session.isGmailConnected = false  // Also update SessionManager
    }
}
