//
//  HistoryView.swift
//  Frontend
//

import SwiftUI

struct HistoryView: View {
    var body: some View {
        ScrollView {
            VStack {
                HStack {
                    Text("Saturday, July 26")
                        .font(.caption)
                        .fontWeight(.bold)
                        .padding(.bottom)
                    Spacer()
                }
                .padding(.horizontal, 12)
                
                HistoryMessageView(title: "Sent email", day: "Jul 26", time: "8:18pm")
                HistoryMessageView(title: "Created invoice", day: "Jul 26", time: "4:20pm")
                
                Rectangle()
                    .foregroundColor(Color(.systemGray6))
                    .frame(height: 4)
                HStack {
                    Text("Friday, July 25")
                        .font(.caption)
                        .fontWeight(.bold)
                        .padding(.top, 8)
                        .padding(.bottom)
                    Spacer()
                }
                .padding(.horizontal, 12)
                
                HistoryMessageView(title: "Sent invoice via email", day: "Jul 25", time: "7:46am")
            }
        }
    }
}

struct HistoryMessageView: View {
    
    var title: String
    var day: String
    var time: String
    
    var body: some View {
        HStack {
            RyderProfileView()
            ZStack {
                RoundedRectangle(cornerRadius: 12)
                    .stroke(Color(.systemGray), lineWidth: 0.5)
                VStack (alignment: .leading){
                    Text(title)
                    HStack (spacing: 4) {
                        Text(day)
                        Text("•")
                        Text(time)
                        Spacer()
                    }
                    .font(.caption)
                    .foregroundColor(.secondary)
                }
                .padding(12)
            }
            .frame(maxWidth: .infinity)
            .frame(height: 68)
        }
        .padding(.horizontal, 12)
    }
}

struct RyderProfileView: View {
    var body: some View {
        ZStack {
            Circle()
                .foregroundColor(Color(red: 32/255, green: 58/255, blue: 250/255))
            Image(systemName: "waveform")
                .resizable()
                .scaledToFit()
                .frame(width: 16, height: 16)
                .foregroundColor(.white)
        }
        .frame(width: 28)
    }
}

#Preview {
    HistoryView()
}
