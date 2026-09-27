import QtQuick 2.15
import SddmComponents 2.0
import QtMultimedia

Rectangle {
  id: root
  width: 1920
  height: 1080

  gradient: Gradient {
      GradientStop { position: 0.0; color: "#050508" }
      GradientStop { position: 1.0; color: "#12101c" }
  }

  property var videos: ["videos/background.mp4", "videos/galaxy.mp4", "videos/particles.mp4", "videos/fluid.mp4", "videos/smooth_wave.mp4", "videos/elegant_dark.mp4", "videos/glowing_lines.mp4", "videos/space_stars.mp4", "videos/neon_minimal.mp4", "videos/abstract_mesh.mp4"]
  property int currentVideoIndex: 0
  
  property int userIndex: userModel.lastIndex >= 0 ? userModel.lastIndex : 0
  property string currentUser: userModel.rowCount() > 0 ? userModel.data(userModel.index(userIndex, 0), userModel.NameRole) : ""
  property int currentSessionIndex: sessionModel.lastIndex >= 0 ? sessionModel.lastIndex : 0

  Connections {
    target: sddm
    function onLoginFailed() { password.text = ""; password.focus = true; box.shake() }
  }

  MediaPlayer {
      id: bgVideo
      source: root.videos[root.currentVideoIndex]
      loops: MediaPlayer.Infinite
      autoPlay: true
      videoOutput: videoOutput
      audioOutput: AudioOutput { muted: true }
  }

  VideoOutput {
      id: videoOutput
      anchors.fill: parent
      fillMode: VideoOutput.PreserveAspectCrop
      opacity: 0.5
  }

  // ==========================================
  // TOP LEFT: WALLPAPER SELECTOR (Premium Pill)
  // ==========================================
  Rectangle {
      width: 260; height: 42
      color: "#0a0a10"
      border.color: "#333344"
      border.width: 1
      radius: 21
      opacity: 0.85
      anchors.top: parent.top
      anchors.left: parent.left
      anchors.margins: 40

      Row {
          anchors.centerIn: parent
          spacing: 25

          Text {
              text: "❮"
              color: leftArrowMouse.containsMouse ? "#00f0ff" : "#888899"
              font.pixelSize: 14
              font.weight: Font.Black
              MouseArea {
                  id: leftArrowMouse
                  anchors.fill: parent; anchors.margins: -10
                  hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                  onClicked: root.currentVideoIndex = (root.currentVideoIndex - 1 + root.videos.length) % root.videos.length
              }
          }

          Text {
              text: "WALLPAPER " + (root.currentVideoIndex + 1)
              color: "#ffffff"
              font.pixelSize: 13
              font.family: "JetBrainsMono Nerd Font"
              font.weight: Font.Bold
              font.letterSpacing: 2
              anchors.verticalCenter: parent.verticalCenter
          }

          Text {
              text: "❯"
              color: rightArrowMouse.containsMouse ? "#00f0ff" : "#888899"
              font.pixelSize: 14
              font.weight: Font.Black
              MouseArea {
                  id: rightArrowMouse
                  anchors.fill: parent; anchors.margins: -10
                  hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                  onClicked: root.currentVideoIndex = (root.currentVideoIndex + 1) % root.videos.length
              }
          }
      }
  }

  // ==========================================
