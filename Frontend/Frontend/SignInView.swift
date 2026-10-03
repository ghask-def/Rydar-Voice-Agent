//
//  SignInView.swift
//  Frontend
//
//  Created by Gabriel Haskell on 7/22/25.
//

import SwiftUI
import FirebaseAuth

struct SignInView: View {
    
    var body: some View {
        VStack {
            
            Text("Rydar")
                .font(.system(size: 28, weight: .bold, design: .rounded))
                .foregroundColor(Color(red: 32/255, green: 58/255, blue: 250/255))
                .padding(.leading)
            
            Text("Automation with ease!")
                .font(.title)
                .fontWeight(.light)
            Spacer()
            Image("signInSelectArt")
                .resizable()
                .scaledToFit()
                .padding(.leading, 36)
            Spacer()
            Button (action: {
                
            }) {
                HStack {
                    Text("Continue with Email")
                }
                .foregroundColor(.white)
                .frame(height: 36)
                .frame(maxWidth: .infinity)
                .background(Color(red: 32/255, green: 58/255, blue: 250/255))
                .cornerRadius(8)
            }
            ZStack {
                Divider()
                    .foregroundColor(Color(.systemGray))
                Text("OR")
                    .font(.subheadline)
                    .foregroundColor(Color(.systemGray))
                    .frame(width: 40)
                    .background(Color(.systemBackground))
            }
            Button (action: {
                GoogleSignInHelper.shared.signIn()
            }) {
                HStack {
                    Image("google")
                        .resizable()
                        .scaledToFit()
                        .frame(width: 24, height: 24)
                        .padding(2)
                        .background(.white)
                        .cornerRadius(4, corners: [.topLeft, .bottomLeft])
                        .padding(.leading, 4)
                    Spacer()
                    Text("Continue with Google")
                    Spacer()
                }
                .foregroundColor(.white)
                .frame(height: 36)
                .frame(maxWidth: .infinity)
                .background(Color(red: 32/255, green: 58/255, blue: 250/255))
                .cornerRadius(8)
            }
        }
        .padding()
    }
}

#Preview {
    SignInView()
}

// MARK: - Custom Rounded Corner Extension
struct RoundedCorner: Shape {
    var radius: CGFloat = .infinity
    var corners: UIRectCorner = .allCorners

    func path(in rect: CGRect) -> Path {
        let path = UIBezierPath(
            roundedRect: rect,
            byRoundingCorners: corners,
            cornerRadii: CGSize(width: radius, height: radius)
        )
        return Path(path.cgPath)
    }
}

extension View {
    func cornerRadius(_ radius: CGFloat, corners: UIRectCorner) -> some View {
        clipShape(RoundedCorner(radius: radius, corners: corners))
    }
}

//struct SignInView: View {
//    var body: some View {
//        VStack(spacing: 20) {
//            Text("Sign In")
//                .font(.largeTitle)
//
//            Button("Sign in with Google") {
//                GoogleSignInHelper.shared.signIn()
//            }
//
////            SignInWithAppleButtonView()
////
////            PhoneAuthView()
//        }
//        .padding()
//    }
//}
