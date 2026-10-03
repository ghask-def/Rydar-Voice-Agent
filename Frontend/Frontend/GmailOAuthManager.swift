import SwiftUI
import AuthenticationServices
import FirebaseAuth

class GmailOAuthManager: NSObject, ObservableObject, ASWebAuthenticationPresentationContextProviding {
    @Published var userEmail = ""
    @Published var isSignedIn = false

    let googleClientId = "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
    let redirectURI = "http://localhost:8000/gmail/google/callback"

    func startOAuthFlow() {
        guard let user = Auth.auth().currentUser else {
            print("User not signed in")
            return
        }

        user.getIDToken { idToken, error in
            guard let idToken = idToken else {
                print("ID Token error: \(error?.localizedDescription ?? "")")
                return
            }
            let payload: [String: Any] = [
                "id_token": idToken,
                "user_id": Auth.auth().currentUser?.uid ?? "NIL"
            ]
            
            var request = URLRequest(url: URL(string: "http://localhost:8000/gmail/google")!)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try? JSONSerialization.data(withJSONObject: payload)

            URLSession.shared.dataTask(with: request) { data, _, error in
                guard let data = data, error == nil else {
                    print("Backend error: \(error?.localizedDescription ?? "")")
                    return
                }

                if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let urlString = json["oauth_url"] as? String,
                   let authURL = URL(string: urlString) {

                    DispatchQueue.main.async {
                        self.launchOAuthSession(authURL: authURL)
                    }
                }
            }.resume()
        }
    }

    private func launchOAuthSession(authURL: URL) {
        let session = ASWebAuthenticationSession(
            url: authURL,
            callbackURLScheme: "com.haskell.frontend"
        ) { callbackURL, error in
            guard let callbackURL = callbackURL else {
                print("OAuth failed or cancelled: \(error?.localizedDescription ?? "")")
                return
            }

            guard let components = URLComponents(url: callbackURL, resolvingAgainstBaseURL: false),
                  let code = components.queryItems?.first(where: { $0.name == "code" })?.value else {
                print("No code in callback")
                return
            }

            self.exchangeCodeForToken(code: code)
        }

        session.presentationContextProvider = self
        session.prefersEphemeralWebBrowserSession = false
        session.start()
    }

    private func exchangeCodeForToken(code: String) {
        let tokenEndpoint = URL(string: "https://oauth2.googleapis.com/token")!
        var request = URLRequest(url: tokenEndpoint)
        request.httpMethod = "POST"
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")

        let params = [
            "code": code,
            "client_id": googleClientId,
            "redirect_uri": redirectURI,
            "grant_type": "authorization_code"
        ]

        let bodyString = params.map { "\($0.key)=\($0.value)" }.joined(separator: "&")
        request.httpBody = bodyString.data(using: .utf8)

        URLSession.shared.dataTask(with: request) { data, _, error in
            guard let data = data, error == nil,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let accessToken = json["access_token"] as? String,
                  let refreshToken = json["refresh_token"] as? String else {
                print("Token exchange failed")
                return
            }

            self.fetchUserEmail(accessToken: accessToken, refreshToken: refreshToken)
        }.resume()
    }

    private func fetchUserEmail(accessToken: String, refreshToken: String) {
        let url = URL(string: "https://www.googleapis.com/oauth2/v2/userinfo")!
        var request = URLRequest(url: url)
        request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")

        URLSession.shared.dataTask(with: request) { data, _, _ in
            guard let data = data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let email = json["email"] as? String else {
                print("Failed to get user email")
                return
            }

            self.sendCredentialsToBackend(email: email, accessToken: accessToken, refreshToken: refreshToken)
        }.resume()
    }

    private func sendCredentialsToBackend(email: String, accessToken: String, refreshToken: String) {
        guard let userID = Auth.auth().currentUser?.uid else {
            print("Missing Firebase user ID")
            return
        }

        let backendURL = URL(string: "http://localhost:8000/gmail/google/store")!
        var request = URLRequest(url: backendURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let payload: [String: Any] = [
            "user_id": userID,
            "email": email,
            "access_token": accessToken,
            "refresh_token": refreshToken,
            "scopes": ["https://www.googleapis.com/auth/gmail.modify"]  // optional
        ]
        print("sending payload")
        request.httpBody = try? JSONSerialization.data(withJSONObject: payload)

        URLSession.shared.dataTask(with: request) { data, _, _ in
            DispatchQueue.main.async {
                self.userEmail = email
                self.isSignedIn = true
            }
        }.resume()
    }


    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        return UIApplication.shared.windows.first { $0.isKeyWindow } ?? ASPresentationAnchor()
    }
}
