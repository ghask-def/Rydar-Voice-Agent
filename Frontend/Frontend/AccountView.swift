//
//  AccountView.swift
//  Frontend
//
//  Created by Gabriel Haskell on 7/15/25.
//
import SwiftUI
import FirebaseAuth


struct AccountView: View {
    
    @EnvironmentObject var sessionManager: SessionManager
    
    var body: some View {
        VStack {
            Circle()
                .foregroundColor(Color(red: 32/255, green: 58/255, blue: 250/255))
                .frame(width: 80, height: 80)
                .padding(.vertical, 8)
            
            Text(Auth.auth().currentUser?.displayName ?? "Your Account")
                .font(.title3)
                .foregroundColor(.primary)
                .padding(.bottom, 1)
            Text(verbatim: Auth.auth().currentUser?.email ?? "")
                .font(.callout)
                .foregroundColor(Color(.systemGray))
                .padding(.bottom)
            
            Button (action: {
                
            }) {
                AccountOptionRowView(icon: "gearshape", title: "Settings")
            }
            Divider()
            AccountOptionRowView(icon: "creditcard", title: "Subscription")
            Divider()
            AccountOptionRowView(icon: "questionmark.circle", title: "Help Center")
            Divider()
            Button (action: {
                sessionManager.signOut()
            }) {
                AccountOptionRowView(icon: "rectangle.portrait.and.arrow.right", title: "Log Out")
            }
            Spacer()
        }
        .padding(8)
    }
}

struct AccountOptionRowView: View {
    var icon: String
    var title: String
    var body: some View {
        HStack {
            Image(systemName: icon)
                .frame(width: 24, height: 24)
            Text(title)
        }
        .font(.callout)
        .foregroundColor(.primary)
        .fontWeight(.medium)
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.vertical, 14)
    }
}
