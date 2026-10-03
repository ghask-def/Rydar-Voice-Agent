import FirebaseAuth
import Foundation

@MainActor
class SessionManager: ObservableObject {
    @Published var isSignedIn = false
    @Published var userID: String? = nil
    @Published var sessionID: String? = nil
    @Published var isGmailConnected: Bool = false

    private var handle: AuthStateDidChangeListenerHandle?

    init() {
        listenToAuthState()
    }

    func listenToAuthState() {
        handle = Auth.auth().addStateDidChangeListener { [weak self] auth, user in
            guard let self = self else { return }

            if let user = user {
                self.isSignedIn = true
                self.userID = user.uid
                self.checkAndAddUserToSupabase(user: user)
                self.checkGmailConnection(for: user.uid)
            } else {
                self.isSignedIn = false
                self.userID = nil
                self.isGmailConnected = false
            }
        }
    }

    func stopListening() {
        if let handle = handle {
            Auth.auth().removeStateDidChangeListener(handle)
        }
    }

    func signOut() {
        try? Auth.auth().signOut()
        isSignedIn = false
        userID = nil
        isGmailConnected = false
    }

    private func checkAndAddUserToSupabase(user: User) {
        SupabaseManager.shared.refreshSession { success in
            if success {
                SupabaseManager.shared.userExists(uid: user.uid) { exists in
                    if !exists {
                        SupabaseManager.shared.sendUserInfo(
                            uuid: user.uid,
                            email: user.email,
                            provider: user.providerData.first?.providerID
                        )
                    } else {
                        print("User already exists in Supabase")
                    }
                }
            } else {
                print("Error refreshing Supabase session")
            }
        }
    }

    private func checkGmailConnection(for userID: String) {
        guard let url = URL(string: "http://localhost:8000/gmail/google/status?user_id=\(userID)") else {
            print("Invalid Gmail status URL")
            return
        }

        URLSession.shared.dataTask(with: url) { [weak self] data, _, error in
            guard let self = self else { return }

            if let error = error {
                print("Error checking Gmail connection: \(error.localizedDescription)")
                return
            }

            guard let data = data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let connected = json["connected"] as? Bool else {
                print("Failed to parse Gmail connection response")
                return
            }

            DispatchQueue.main.async {
                self.isGmailConnected = connected
                print("Gmail connected: \(connected)")
            }
        }.resume()
    }
}
