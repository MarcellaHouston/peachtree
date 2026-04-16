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
    // common variables
    var audioRecorder: AVAudioRecorder?
    var isRecording = false
    var summary: String = ""
    var transcription: String = ""
    var showReview = false
    var isUploading = false
    
    //var for server ip address
    private let backendIP = "34.192.65.138"
    
    //press the button to record, press again to stop
    func toggleRecording(at endpoint: AudioEndpoint) {
        if isRecording {
            stopRecording(at: endpoint)
        } else {
            startRecording()
        }
    }
    
    //recording function
    private func startRecording() {
        let session = AVAudioSession.sharedInstance()
        //to account for older ios versions
        
        //removed call for "requestRecordPermission
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
            
            self.isRecording = true
        } catch {
            print("Recording failed: \(error)")
        }
    }
    
    
    private func stopRecording(at endpoint: AudioEndpoint) {
        audioRecorder?.stop()
        isRecording = false
        
        // CHANGE THIS:
        if let url = audioRecorder?.url {
            startUpload(at: endpoint, fileURL: url)
        }
    }
    
    func startUpload(at endpoint: AudioEndpoint, fileURL: URL) {
        //show analyzing
        self.isUploading = true
        
        //start the actual network request
        self.uploadAudio(to: endpoint, fileURL: fileURL)
    }
    
    
    // the network request to send file to backend
    private func uploadAudio(to endpoint: AudioEndpoint, fileURL: URL) {
        
        self.isUploading = true // Direct update
    
        // holds info about which endpoint the request is going to
        let endpointConfig = endpoint.config
        
        // using the url from AudioEndpoint enum
        var request = URLRequest(url: endpointConfig.url)
    
        request.httpMethod = "POST"
        request.timeoutInterval = 240
        request.setValue("application/octet-stream", forHTTPHeaderField: "Content-Type")
        request.setValue(UserCreds.shared.getToken(), forHTTPHeaderField: "Authorization")
        request.setValue(String(UserCreds.shared.getIntId() ?? -1), forHTTPHeaderField: "User-ID")
        request.setValue(UserCreds.shared.getStringId(), forHTTPHeaderField: "Username")
        request.setValue(".m4a", forHTTPHeaderField: "File-Type")
    
        // add any additional headers needed for goal guidance or nlp
        if let params = endpointConfig.extraParameters {
            for (key, value) in params {
                request.setValue("\(value)", forHTTPHeaderField: key)
            }
        }
        
        // try to send the audio to the backedn
        do {
            let audioData = try Data(contentsOf: fileURL)
            request.httpBody = audioData
            
            URLSession.shared.dataTask(with: request) { data, response, error in
                self.isUploading = false // Direct update
                
                if let error = error {
                    print("Upload failed: \(error.localizedDescription)")
                    return
                }
                
                if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200, let data = data {
                    do {
                        if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                            // TODO: add other results for guidance and NLP
                            self.summary = "\(json["summary"] ?? json["changes_summary"] ?? "No summary available.")"
                            self.transcription = "\(json["transcription"] ?? "No transcription available.")"
                            self.showReview = true
                        }
                    } catch {
                        print("JSON decoding failed: \(error)")
                    }
                }
            }.resume()
            
        } catch {
            print("Could not read audio file: \(error)")
            self.isUploading = false
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
            "user_id": UserCreds.shared.getStringId() as Any,
            "transcription": self.transcription
        ]
        
        // convert to json data
        do {
            let jsonData = try JSONSerialization.data(withJSONObject: body)
            request.httpBody = jsonData
            
            //print("Saving conversation for user: " + UserCreds.shared.getStringId())
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

struct UploadConfig {
    let url: URL
    let extraParameters: [String: Any]?
}

enum AudioEndpoint {
    case goalGuidance(goalId: Int)
    case endOfDay
    case nlp

    var config: UploadConfig {
        let baseUrl = URL(string: "http://34.192.65.138:80")!
        
        switch self {
        case .goalGuidance(let id):
            return UploadConfig(
                url: baseUrl.appendingPathComponent("/goal_guidance"),
                extraParameters: ["goal_id": id]
            )
        case .endOfDay:
            return UploadConfig(
                url: baseUrl.appendingPathComponent("/stt/eod_summary"),
                extraParameters: nil
            )
        case .nlp:
            return UploadConfig(
                url: baseUrl.appendingPathComponent("/extract_goal"),
                extraParameters: nil
            )
        }
    }
}
