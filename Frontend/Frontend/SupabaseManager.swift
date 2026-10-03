//
//  SupabaseManager.swift
//  Frontend
//
//  Created by Gabriel Haskell on 7/22/25.
//

import Foundation
import FirebaseAuth

class SupabaseManager {
    static let shared = SupabaseManager()

    private let baseURL = URL(string: "https://YOUR-PROJECT.supabase.co/rest/v1/")!
    private let anonKey = "YOUR_SUPABASE_ANON_KEY"

    private var jwtToken: String?

    private var defaultHeaders: [String: String] {
        guard let token = jwtToken else {
            print("Firebase JWT Token is missing.")
            return [:]
        }
        return [
            "apikey": anonKey,
            "Authorization": "Bearer \(jwtToken ?? "")",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        ]
    }
    
    /// Call this after Firebase login to sync token to Supabase
    func refreshSession(completion: @escaping (Bool) -> Void) {
        guard let user = Auth.auth().currentUser else {
            print("No Firebase user is signed in.")
            completion(false)
            return
        }

        user.getIDToken { token, error in
            if let error = error {
                print("Failed to get Firebase ID token: \(error.localizedDescription)")
                completion(false)
                return
            }

            self.jwtToken = token
            print("Firebase JWT token set for Supabase requests.")
            completion(true)
        }
    }

    

    // MARK: - Public Methods

    func sendUserInfo(uuid: String, email: String?, provider: String?) {
        print(defaultHeaders)
        let body: [String: Any] = [
            "user_id": uuid,
//            "email": email ?? "",
////            "phone": phone ?? "",
//            "provider": provider ?? ""
        ]

        request(
            endpoint: "users",
            method: "POST",
            body: body
        )
        
    }

    func updateUserInfo(uid: String, updates: [String: Any]) {
        request(
            endpoint: "users?user_id=eq.\(uid)",
            method: "PATCH",
            body: updates
        )
    }

    func deleteUser(uid: String) {
        request(
            endpoint: "users?user_id=eq.\(uid)",
            method: "DELETE"
        )
    }

    // MARK: - Private Request Builder

    private func request(endpoint: String,
                         method: String,
                         body: [String: Any]? = nil) {
        guard let url = URL(string: endpoint, relativeTo: baseURL) else {
            print("Invalid Supabase URL")
            return
        }
        
        print(url)

        var request = URLRequest(url: url)
        request.httpMethod = method
        defaultHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }

        if let body = body {
            request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        }

        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("Supabase request error: \(error.localizedDescription)")
                return
            }

            guard let httpResponse = response as? HTTPURLResponse else {
                print("No valid response from Supabase")
                return
            }

            if httpResponse.statusCode >= 200 && httpResponse.statusCode < 300 {
                print("Supabase request successful: \(httpResponse.statusCode)")
            } else {
                print("Supabase error: \(httpResponse.statusCode)")
                if let data = data, let str = String(data: data, encoding: .utf8) {
                    print("Response: \(str)")
                }
            }
        }.resume()
    }
    
    func userExists(uid: String, completion: @escaping (Bool) -> Void) {
        guard let url = URL(string: "users?user_id=eq.\(uid)", relativeTo: baseURL) else {
            completion(false)
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        defaultHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }

        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("Error checking user existence: \(error.localizedDescription)")
                completion(false)
                return
            }

            guard let data = data else {
                print("No data received from Supabase")
                completion(false)
                return
            }

            do {
                print(data)
                let result = try JSONDecoder().decode([UserInfo].self, from: data)
                completion(!result.isEmpty)
            } catch {
                print("JSON decode error: \(error.localizedDescription)")
                completion(false)
            }
        }.resume()
    }

}
