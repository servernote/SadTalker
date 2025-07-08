import SwiftUI
import AVKit

struct ContentView: View {
    @State private var videoURL: URL?
    @State private var isLoading = false

    var body: some View {
        VStack {
            if let videoURL = videoURL {
                VideoPlayer(player: AVPlayer(url: videoURL))
                    .frame(height: 300)
            }

            Button("アップロードして動画生成") {
                Task {
                    await uploadAndFetchVideo()
                }
            }
            .disabled(isLoading)
            .padding()

            if isLoading {
                ProgressView("生成中...")
            }
        }
    }

    func uploadAndFetchVideo() async {
        guard let image = UIImage(named: "face_sample"),
              let imageData = image.jpegData(compressionQuality: 0.8),
              let audioURL = Bundle.main.url(forResource: "voice_sample", withExtension: "wav")
        else {
            print("画像または音声が見つかりません")
            return
        }

        isLoading = true
        defer { isLoading = false }

        let boundary = "Boundary-\(UUID().uuidString)"
        var request = URLRequest(url: URL(string: "https://voicetech.jorudan.co.jp/sadtalker_api/generate")!)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()

        // 画像パート
        body.append("--\(boundary)\r\n")
        body.append("Content-Disposition: form-data; name=\"source_image\"; filename=\"image.jpg\"\r\n")
        body.append("Content-Type: image/jpeg\r\n\r\n")
        body.append(imageData)
        body.append("\r\n")

        // 音声パート
        if let audioData = try? Data(contentsOf: audioURL) {
            body.append("--\(boundary)\r\n")
            body.append("Content-Disposition: form-data; name=\"driven_audio\"; filename=\"audio.wav\"\r\n")
            body.append("Content-Type: audio/wav\r\n\r\n")
            body.append(audioData)
            body.append("\r\n")
        }

        body.append("--\(boundary)--\r\n")

        do {
            let (data, response) = try await URLSession.shared.upload(for: request, from: body)
            guard let httpResp = response as? HTTPURLResponse, httpResp.statusCode == 200 else {
                print("エラー: サーバー応答 \(response)")
                return
            }

            // 一時ファイルに保存
            let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent("result.mp4")
            try data.write(to: tempURL)
            videoURL = tempURL

        } catch {
            print("アップロードエラー: \(error)")
        }
    }
}

// ヘルパー：Data拡張
extension Data {
    mutating func append(_ string: String) {
        if let data = string.data(using: .utf8) {
            append(data)
        }
    }
}
