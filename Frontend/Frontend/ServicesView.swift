//
//  NotificationsView.swift
//  Frontend
//

import SwiftUI

struct ServicesView: View {
    var body: some View {
        ScrollView {
            VStack {
                HStack {
                    Text("Try our latest")
                        .font(.subheadline)
                        .fontWeight(.bold)
                    Spacer()
                }
                .padding(.horizontal, 12)
                
                HStack(spacing: 0) {
                    ZStack {
                        Rectangle()
                            .fill(Color(red: 150/255, green: 163/255, blue: 250/255)) // Just for visibility
                        VStack (alignment: .leading){
                            HStack {
                                Text("Invoice with ease: payment has never been more simple")
                                    .foregroundColor(.white)
                                    .font(.subheadline)
                                    .fontWeight(.bold)
                                Spacer()
                            }
                            Spacer()
                            Text("Invoice with Ryder")
                                .font(.caption)
                                .fontWeight(.medium)
                                .padding(8)
                                .background()
                                .cornerRadius(16)
                        }
                        .padding(12)
                    }
                        .frame(maxHeight: .infinity)

                    Image("invoice_image")
                        .resizable()
                        .scaledToFit()
                        .frame(maxHeight: .infinity)
                }
                .frame(height: 150)
                .frame(maxWidth: .infinity)
                .background(
                    GeometryReader { geometry in
                        Color.clear
                            .overlay(
                                HStack(spacing: 0) {
                                    Rectangle()
                                        .fill(Color.gray)
                                        .frame(width: geometry.size.width * 2 / 3)

                                    Image("invoice_image")
                                        .resizable()
                                        .scaledToFit()
                                        .frame(width: geometry.size.width / 3, height: 120)
                                }
                            )
                    }
                )
                .cornerRadius(12)
                .padding(.horizontal, 12)
                .padding(.bottom, 20)
                HStack (spacing: 12) {
                    ZStack {
                        Rectangle()
                            .foregroundColor(Color(.systemGray6))
                        VStack {
                            Spacer()
                            HStack {
                                Text("Navigation")
                                    .font(.caption)
                                    .fontWeight(.medium)
                                Spacer()
                            }
                        }
                        .padding(8)
                        HStack {
                            Spacer()
                            Image("navigation_image")
                                .resizable()
                                .scaledToFit()
                                .frame(width: 60, height: 60)
                                .padding()
                        }
                    }
                    .frame(height: 100)
                    .cornerRadius(12)
                    ZStack {
                        Rectangle()
                            .foregroundColor(Color(.systemGray6))
                        VStack {
                            Spacer()
                            HStack {
                                Text("Email")
                                    .font(.caption)
                                    .fontWeight(.medium)
                                Spacer()
                            }
                        }
                        .padding(8)
                        HStack {
                            Spacer()
                            Image("email_image")
                                .resizable()
                                .scaledToFit()
                                .frame(width: 60, height: 60)
                                .padding()
                        }
                    }
                    .frame(height: 100)
                    .cornerRadius(12)
                }
                .padding(.horizontal, 12)
                Spacer()
                    .frame(height: 40)
                Rectangle()
                    .foregroundColor(Color(.systemGray6))
                    .frame(height: 4)
                
            }
        }
    }
}

#Preview {
    ServicesView()
}
