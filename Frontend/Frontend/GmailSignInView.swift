//
//  GmailSignInView.swift
//  Frontend
//
//  Created by Gabriel Haskell on 7/15/25.
//

import SwiftUI

struct GmailSignInView: View {
    @Binding var isSignedIn: Bool
    @Binding var userEmail: String
    @Binding var gmailEnabled: Bool
    @Environment(\.dismiss) private var dismiss
    @State private var email = ""
    @State private var password = ""
    @State private var isLoading = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                Image(systemName: "envelope.fill")
                    .font(.system(size: 60))
                    .foregroundColor(.red)
                
                Text("Sign in to Gmail")
                    .font(.title2)
                    .fontWeight(.bold)
                
                Text("Connect your Gmail account to enable email integration")
                    .font(.body)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
                
                VStack(spacing: 16) {
                    TextField("Email", text: $email)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .keyboardType(.emailAddress)
                        .autocapitalization(.none)
                    
                    SecureField("Password", text: $password)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                }
                .padding(.horizontal)
                
                Button(action: signIn) {
                    if isLoading {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                    } else {
                        Text("Sign In")
                            .fontWeight(.semibold)
                    }
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.blue)
                .foregroundColor(.white)
                .cornerRadius(10)
                .padding(.horizontal)
                .disabled(email.isEmpty || password.isEmpty || isLoading)
                
                Spacer()
            }
            .padding()
            .navigationTitle("Gmail Sign In")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Cancel") {
                        gmailEnabled = false
                        dismiss()
                    }
                }
            }
        }
    }
    
    private func signIn() {
        isLoading = true
        
        // Simulate API call
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
            isLoading = false
            
            // Simulate successful sign in
            if !email.isEmpty && !password.isEmpty {
                isSignedIn = true
                userEmail = email
                dismiss()
            }
        }
    }
}
