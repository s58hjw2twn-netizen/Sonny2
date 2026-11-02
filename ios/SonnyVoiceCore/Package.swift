// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "SonnyVoiceCore",
    platforms: [.iOS(.v17)],
    products: [.library(name: "SonnyVoiceCore", targets: ["SonnyVoiceCore"])],
    targets: [
        .target(name: "SonnyVoiceCore"),
        .testTarget(name: "SonnyVoiceCoreTests", dependencies: ["SonnyVoiceCore"]),
    ]
)
