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

  // ==========================================
  // VIDEO BACKGROUND (Fallback to Gradient if missing)
  // ==========================================
  MediaPlayer {
      id: bgVideo
      source: "background.mp4"
      loops: MediaPlayer.Infinite
      autoPlay: true
      videoOutput: videoOutput
      audioOutput: AudioOutput { muted: true } // Mute the video just in case
  }

  VideoOutput {
      id: videoOutput
      anchors.fill: parent
      fillMode: VideoOutput.PreserveAspectCrop
      opacity: 0.5 // Hace que el video se mezcle con el fondo oscuro y no deslumbre
  }

  property int userIndex: userModel.lastIndex >= 0 ? userModel.lastIndex : 0
  property string currentUser: userModel.rowCount() > 0 ? userModel.data(userModel.index(userIndex, 0), userModel.NameRole) : ""
  property int currentSessionIndex: sessionModel.lastIndex >= 0 ? sessionModel.lastIndex : 0

  Connections {
    target: sddm
    function onLoginFailed() { password.text = ""; password.focus = true; box.shake() }
  }

  // ==========================================
  // TOP RIGHT: CLOCK & DATE
  // ==========================================
  Column {
      anchors.top: parent.top
      anchors.right: parent.right
      anchors.margins: 50
      spacing: 5
      
      Text {
          id: timeDisplay
          text: Qt.formatTime(new Date(), "HH:mm:ss")
          color: "#00f0ff"
          font.pixelSize: 48
          font.family: "JetBrainsMono Nerd Font"
          font.weight: Font.Black
          anchors.right: parent.right
          
          Timer {
              interval: 1000; running: true; repeat: true
              onTriggered: timeDisplay.text = Qt.formatTime(new Date(), "HH:mm:ss")
          }
      }
      
      Text {
          id: dateDisplay
          text: Qt.formatDate(new Date(), "dd MMM yyyy").toUpperCase()
          color: "#ffffff"
          font.pixelSize: 18
          font.family: "JetBrainsMono Nerd Font"
          font.letterSpacing: 2
          anchors.right: parent.right
          opacity: 0.7
          
          Timer {
              interval: 60000; running: true; repeat: true
              onTriggered: dateDisplay.text = Qt.formatDate(new Date(), "dd MMM yyyy").toUpperCase()
          }
      }
  }

  // ==========================================
  // CENTER: LOGIN HUD
  // ==========================================
  Column {
      anchors.centerIn: parent
      spacing: 60

      Item {
          width: 500
          height: 120
          anchors.horizontalCenter: parent.horizontalCenter
          
          Text {
              text: "X64 LIOS"
              color: "#ff007f"
              font.family: "JetBrainsMono Nerd Font"
              font.pixelSize: 85
              font.weight: Font.Black
              font.letterSpacing: 15
              anchors.centerIn: parent
              anchors.horizontalCenterOffset: -4
              anchors.verticalCenterOffset: 3
              opacity: 0.8
          }
          Text {
              text: "X64 LIOS"
              color: "#00f0ff"
              font.family: "JetBrainsMono Nerd Font"
              font.pixelSize: 85
              font.weight: Font.Black
              font.letterSpacing: 15
              anchors.centerIn: parent
              anchors.horizontalCenterOffset: 4
              anchors.verticalCenterOffset: -3
              opacity: 0.8
          }
          Text {
              text: "X64 LIOS"
              color: "#ffffff"
              font.family: "JetBrainsMono Nerd Font"
              font.pixelSize: 85
              font.weight: Font.Black
              font.letterSpacing: 15
              anchors.centerIn: parent
          }
          
          Rectangle {
              width: 120
              height: 4
              color: "#00ffcc"
              anchors.bottom: parent.bottom
              anchors.horizontalCenter: parent.horizontalCenter
              SequentialAnimation on opacity {
                  loops: Animation.Infinite
                  NumberAnimation { to: 0.2; duration: 1500; easing.type: Easing.InOutSine }
                  NumberAnimation { to: 1.0; duration: 1500; easing.type: Easing.InOutSine }
              }
          }
      }

      Column {
          spacing: 15
          anchors.horizontalCenter: parent.horizontalCenter

          Text {
              text: "S Y S T E M   O P E R A T O R"
              color: "#555566"
              font.pixelSize: 12
              font.family: "JetBrainsMono Nerd Font"
              font.weight: Font.Bold
              anchors.horizontalCenter: parent.horizontalCenter
          }

          Row {
              anchors.horizontalCenter: parent.horizontalCenter
              spacing: 20

              Text {
                  text: "<"
                  color: userModel.rowCount() > 1 ? "#00f0ff" : "#333344"
                  font.pixelSize: 26
                  font.family: "JetBrainsMono Nerd Font"
                  font.weight: Font.Black
                  anchors.verticalCenter: parent.verticalCenter
                  MouseArea {
                      anchors.fill: parent
                      enabled: userModel.rowCount() > 1
                      cursorShape: Qt.PointingHandCursor
                      onClicked: {
                          root.userIndex = (root.userIndex - 1 + userModel.rowCount()) % userModel.rowCount()
                      }
                  }
              }

              Text {
                  text: root.currentUser.toUpperCase()
                  color: "#ffffff"
                  font.pixelSize: 26
                  font.family: "JetBrainsMono Nerd Font"
                  font.weight: Font.Black
                  font.letterSpacing: 4
                  anchors.verticalCenter: parent.verticalCenter
              }

              Text {
                  text: ">"
                  color: userModel.rowCount() > 1 ? "#00f0ff" : "#333344"
                  font.pixelSize: 26
                  font.family: "JetBrainsMono Nerd Font"
                  font.weight: Font.Black
                  anchors.verticalCenter: parent.verticalCenter
                  MouseArea {
                      anchors.fill: parent
                      enabled: userModel.rowCount() > 1
                      cursorShape: Qt.PointingHandCursor
                      onClicked: {
                          root.userIndex = (root.userIndex + 1) % userModel.rowCount()
                      }
                  }
              }
          }
      }

      Rectangle {
          id: box
          width: 320
          height: 60
          color: "#0a0a10"
          radius: 8
          border.width: 2
          anchors.horizontalCenter: parent.horizontalCenter

          SequentialAnimation on border.color {
              loops: Animation.Infinite
              ColorAnimation { to: "#ff007f"; duration: 3000 }
              ColorAnimation { to: "#7000ff"; duration: 3000 }
              ColorAnimation { to: "#00f0ff"; duration: 3000 }
              ColorAnimation { to: "#ff007f"; duration: 3000 }
          }

          SequentialAnimation {
              id: shakeAnim
              NumberAnimation { target: box; property: "anchors.horizontalCenterOffset"; to: -10; duration: 50 }
              NumberAnimation { target: box; property: "anchors.horizontalCenterOffset"; to: 10; duration: 50 }
              NumberAnimation { target: box; property: "anchors.horizontalCenterOffset"; to: -10; duration: 50 }
              NumberAnimation { target: box; property: "anchors.horizontalCenterOffset"; to: 10; duration: 50 }
              NumberAnimation { target: box; property: "anchors.horizontalCenterOffset"; to: 0; duration: 50 }
          }

          function shake() { shakeAnim.start() }

          TextInput {
              id: password
              anchors.fill: parent
              horizontalAlignment: TextInput.AlignHCenter
              verticalAlignment: TextInput.AlignVCenter
              echoMode: TextInput.Password
              font.pixelSize: 24
              color: "#ffffff"
              passwordCharacter: "■"
              focus: true
              
              Text {
                  anchors.centerIn: parent
                  text: "ACCESS CODE"
                  color: "#444455"
                  font.pixelSize: 14
                  font.letterSpacing: 2
                  font.family: "JetBrainsMono Nerd Font"
                  visible: password.text.length === 0 && !password.activeFocus
              }

              Keys.onPressed: {
                  if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                      sddm.login(root.currentUser, password.text, root.currentSessionIndex)
                      event.accepted = true
                  }
              }
          }
      }
  }

  // ==========================================
  // BOTTOM LEFT: SESSION SELECTOR
  // ==========================================
  Row {
      anchors.bottom: parent.bottom
      anchors.left: parent.left
      anchors.margins: 50
      spacing: 15

      Text {
          text: "[ SESSION ]"
          color: "#00f0ff"
          font.pixelSize: 14
          font.family: "JetBrainsMono Nerd Font"
          font.weight: Font.Bold
          anchors.verticalCenter: parent.verticalCenter
      }

      Text {
          text: sessionModel.rowCount() > 0 ? sessionModel.data(sessionModel.index(root.currentSessionIndex, 0), sessionModel.NameRole) : "X64 Desktop"
          color: "#ffffff"
          font.pixelSize: 16
          font.family: "JetBrainsMono Nerd Font"
          font.weight: Font.Bold
          anchors.verticalCenter: parent.verticalCenter
          
          MouseArea {
              anchors.fill: parent
              cursorShape: Qt.PointingHandCursor
              onClicked: {
                  if (sessionModel.rowCount() > 0) {
                      root.currentSessionIndex = (root.currentSessionIndex + 1) % sessionModel.rowCount()
                  }
              }
          }
      }
  }

  // ==========================================
  // BOTTOM RIGHT: POWER CONTROLS
  // ==========================================
  Row {
      anchors.bottom: parent.bottom
      anchors.right: parent.right
      anchors.margins: 50
      spacing: 20

      Rectangle {
          width: 140; height: 42
          color: rebootMouse.containsMouse ? "#222233" : "#111116"
          border.color: rebootMouse.containsMouse ? "#00f0ff" : "#333344"
          border.width: 2
          radius: 6
          Text {
              anchors.centerIn: parent
              text: "REBOOT"
              color: rebootMouse.containsMouse ? "#00f0ff" : "#aaaaaa"
              font.pixelSize: 14
              font.family: "JetBrainsMono Nerd Font"
              font.weight: Font.Bold
              font.letterSpacing: 2
          }
          MouseArea {
              id: rebootMouse
              anchors.fill: parent
              hoverEnabled: true
              cursorShape: Qt.PointingHandCursor
              onClicked: sddm.reboot()
          }
      }

      Rectangle {
          width: 140; height: 42
          color: powerMouse.containsMouse ? "#331111" : "#111116"
          border.color: powerMouse.containsMouse ? "#ff007f" : "#333344"
          border.width: 2
          radius: 6
          Text {
              anchors.centerIn: parent
              text: "SHUTDOWN"
              color: powerMouse.containsMouse ? "#ff007f" : "#aaaaaa"
              font.pixelSize: 14
              font.family: "JetBrainsMono Nerd Font"
              font.weight: Font.Bold
              font.letterSpacing: 2
          }
          MouseArea {
              id: powerMouse
              anchors.fill: parent
              hoverEnabled: true
              cursorShape: Qt.PointingHandCursor
              onClicked: sddm.powerOff()
          }
      }
  }

  Component.onCompleted: password.forceActiveFocus()
}
