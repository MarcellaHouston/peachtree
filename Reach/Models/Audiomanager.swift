//
//  AudioManager.swift
//  Reach
//
//  Created by Shahd Alghurbani on 3/25/26.
//

import Foundation
import AVFoundation
import Observation

@Observable
class AudioManager: NSObject {
    var audioRecorder: AVAudioRecorder?
    var isRecording = false
    var summary: String = ""
    var transcription: String = ""
    var showReview = false
    var isUploading = false
    
    //var for server ip address
    private let backendIP = "34.192.65.138"
    
    //press the button to record, press again to stop
    func toggleRecording() {
        if isRecording {
            stopRecording()
        } else {
            startRecording()
        }
    }
    
    //recording function
    private func startRecording() {
        let session = AVAudioSession.sharedInstance()
        //to account for older ios versions
        if #available(iOS 17.0, *) {
            AVAudioApplication.requestRecordPermission { granted in
                guard granted else { return }
                do {
                    try session.setCategory(.playAndRecord, mode: .default)
                    try session.setActive(true)
                    
                    let path = FileManager.default.temporaryDirectory.appendingPathComponent("reflection.m4a")
                    let settings: [String: Any] = [
                        AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
                        AVSampleRateKey: 12000,
                        AVNumberOfChannelsKey: 1,
                        AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
                    ]
                    
                    self.audioRecorder = try AVAudioRecorder(url: path, settings: settings)
                    self.audioRecorder?.record()
                    
                  
                    DispatchQueue.main.async { self.isRecording = true }
                    
                    //if it didnt record properly
                } catch {
                    print("Recording failed: \(error)")
                }
            }
            
        } else {
            session.requestRecordPermission { granted in
                guard granted else { return }
                do {
                    try session.setCategory(.playAndRecord, mode: .default)
                    try session.setActive(true)
                    
                    let path = FileManager.default.temporaryDirectory.appendingPathComponent("reflection.m4a")
                    let settings: [String: Any] = [
                        AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
                        AVSampleRateKey: 12000,
                        AVNumberOfChannelsKey: 1,
                        AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
                    ]
                    
                    self.audioRecorder = try AVAudioRecorder(url: path, settings: settings)
                    self.audioRecorder?.record()
                    
                    // UI updates must stay on the main thread
                    DispatchQueue.main.async { self.isRecording = true }
                } catch {
                    print("Recording failed: \(error)")
                }
            }
        }
    }
    
    private func stopRecording() {
            audioRecorder?.stop()
            isRecording = false
            
            // CHANGE THIS:
            if let url = audioRecorder?.url {
                startUpload(fileURL: url)
            }
        }
    
    func startUpload(fileURL: URL) {
           //show analyzing
            DispatchQueue.main.async {
                self.isUploading = true
            }
            
            // 2. Start the actual network request
            self.uploadAudio(fileURL: fileURL)
        }
    
    
    // the network request to send file to backend
    private func uploadAudio(fileURL: URL) {
        
        //guard let url = URL(string: "http://\(backendIP):5000/stt/eod_summary") else { return }
        guard let url = URL(string: "http://\(backendIP):80/stt/eod_summary") else { return }
        
        // Start loading state
        DispatchQueue.main.async { self.isUploading = true }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = 1000
        request.setValue("application/octet-stream", forHTTPHeaderField: "Content-Type")
        
        request.setValue("Reach staff", forHTTPHeaderField: "User-ID")
        request.setValue(".m4a", forHTTPHeaderField: "File-Type")
        
        do {
            let audioData = try Data(contentsOf: fileURL)
            print("reached endpoint")
            request.httpBody = audioData
            print(audioData)
            
            let task = URLSession.shared.dataTask(with: request) { data, response, error in
                // Stop loading state regardless of outcome
                DispatchQueue.main.async { self.isUploading = false }
                
                if let error = error {
                    print("Upload failed: \(error.localizedDescription)")
                    return
                }
                
                if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200, let data = data {
                    print("Server responded with status: 200")
                    
                    
                    do {
                        // Decode JSON response from the backend
                        if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                            
                            // update ui variables
                            DispatchQueue.main.async {
                                self.summary = "\(json["summary"] ?? "No summary available.")"
                                self.transcription = "\(json["transcription"] ?? "No transcription available.")"
                                //  screen swap in ui
                                self.showReview = true
                                
                            }
                        }
                        else
                        {
                            print("oh no")
                        }
                        
                    } catch {
                        print("JSON decoding failed: \(error)")
                    }
                }
            }
            
            task.resume()
            
        } catch {
            print("Could not read audio file: \(error)")
            DispatchQueue.main.async { self.isUploading = false }
        }
    }
    
    // save function so back end saves it after user presses "looks good"
    
    func saveConversation() {
        guard let url = URL(string: "http://\(backendIP):80/stt/save_convo") else { return }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        // sending json
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // create data dictionary based on python variables
        let body: [String: Any] = [
            "user_id": "Reach staff",
            "transcription": self.transcription
        ]
        
        // convert to json data
        do {
            let jsonData = try JSONSerialization.data(withJSONObject: body)
            request.httpBody = jsonData
            
            print("Saving conversation for user: Reach staff")
        } catch {
            print("Failed to encode JSON: \(error)")
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let httpResponse = response as? HTTPURLResponse {
                print("Save status: \(httpResponse.statusCode)")
            }
        }.resume()
        
        // Reset UI state to go back to original screen
        self.showReview = false
    }
}
