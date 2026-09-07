import SwiftUI
import UserNotifications

@main
struct PersonalAICompanionApp: App {
    @StateObject private var store = CompanionStore()
    @Environment(\.scenePhase) private var scenePhase

    init() {
        BackgroundCoordinator.shared.register { }
        UNUserNotificationCenter.current().requestAuthorization(options:[.alert,.sound,.badge]) { _,_ in }
    }

    var body: some Scene {
        WindowGroup {
            NavigationStack {
                Form {
                    Section("Personal AI computer") {
                        TextField("https://your-computer:8766",text:$store.baseURL)
                            .textInputAutocapitalization(.never).keyboardType(.URL)
                        Toggle("Allow insecure local development",isOn:$store.allowInsecureDevelopment)
                        if store.allowInsecureDevelopment {
                            Text("Development only. HTTP/WS exposes pairing and bearer credentials to the local network.")
                                .font(.caption).foregroundStyle(.orange)
                        }
                    }
                    Section("Secure pairing") {
                        TextField("Pairing token from desktop",text:$store.pairingToken)
                            .textInputAutocapitalization(.never)
                        TextField("6-digit code",text:$store.pairingCode).keyboardType(.numberPad)
                        Button("Pair iPhone") { Task { await store.pair() } }
                    }
                    Section("Connection") {
                        LabeledContent("Status",value:store.status)
                        LabeledContent("Channel",value:store.connected ? "Connected" : "Offline")
                        HStack {
                            Button("Connect") { store.connect() }
                            Button("Disconnect",role:.cancel) { store.disconnect() }
                        }
                    }
                    Section("Voice") {
                        Toggle("Active voice session",isOn:Binding(get:{store.voiceActive},set:{ value in Task { await store.setVoiceActive(value) }}))
                        Text("Background audio is used only while an active voice session is running. Ordinary device connectivity follows iOS lifecycle rules.")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                    Section("Security") {
                        Text("Device ID and bearer token are stored in the iPhone Keychain with this-device-only protection.")
                            .font(.caption)
                        Button("Forget this iPhone",role:.destructive) { store.forgetDevice() }
                    }
                }
                .navigationTitle("Personal AI")
            }
            .onAppear { if store.deviceID != nil { store.connect() } }
            .onChange(of:scenePhase) { _,phase in
                if phase == .active { store.connect() }
                if phase == .background { BackgroundCoordinator.shared.schedule() }
            }
        }
    }
}
