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
  // ==========================================
  // TOP RIGHT: CLOCK, DATE & HARDWARE HUD
  // ==========================================
  Column {
      anchors.top: parent.top
      anchors.right: parent.right
      anchors.margins: 40
      spacing: 15
      
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
          font.pixelSize: 16
          font.family: "JetBrainsMono Nerd Font"
          font.letterSpacing: 2
          anchors.right: parent.right
          opacity: 0.7
          
          Timer {
              interval: 60000; running: true; repeat: true
              onTriggered: dateDisplay.text = Qt.formatDate(new Date(), "dd MMM yyyy").toUpperCase()
          }
      }
      
      // Unified System & Hardware HUD Widget
      Rectangle {
          width: 270
          height: sysCol.implicitHeight + 40
          color: "#0a0a10"
          border.color: "#333344"
          border.width: 1
          radius: 12
          opacity: 0.85
          anchors.right: parent.right
          
          Column {
              id: sysCol
              anchors.centerIn: parent
              spacing: 12
              
              // --- SYSTEM INFO ---
              Text { text: "SYSTEM INFO"; color: "#555566"; font.pixelSize: 12; font.family: "JetBrainsMono Nerd Font"; font.weight: Font.Bold; anchors.horizontalCenter: parent.horizontalCenter }
              
              Row {
                  spacing: 12
                  Text { width: 22; text: ""; color: "#00f0ff"; font.pixelSize: 18; font.family: "JetBrainsMono Nerd Font"; horizontalAlignment: Text.AlignHCenter; anchors.verticalCenter: parent.verticalCenter }
                  Text { text: "X64 LIOS"; color: "#ffffff"; font.pixelSize: 15; font.family: "JetBrainsMono Nerd Font"; font.weight: Font.Bold; anchors.verticalCenter: parent.verticalCenter }
              }
              Row {
                  spacing: 12
                  Text { width: 22; text: "󰒋"; color: "#00ffcc"; font.pixelSize: 18; font.family: "JetBrainsMono Nerd Font"; horizontalAlignment: Text.AlignHCenter; anchors.verticalCenter: parent.verticalCenter }
                  Text { text: (typeof sddm !== "undefined" && sddm.hostName && sddm.hostName !== "") ? sddm.hostName : "x64-machine"; color: "#ffffff"; font.pixelSize: 15; font.family: "JetBrainsMono Nerd Font"; font.weight: Font.Bold; anchors.verticalCenter: parent.verticalCenter }
              }
              Row {
                  spacing: 12
                  Text { width: 22; text: "󰌽"; color: "#ff007f"; font.pixelSize: 18; font.family: "JetBrainsMono Nerd Font"; horizontalAlignment: Text.AlignHCenter; anchors.verticalCenter: parent.verticalCenter }
                  Text { text: "Linux CachyOS"; color: "#ffffff"; font.pixelSize: 15; font.family: "JetBrainsMono Nerd Font"; font.weight: Font.Bold; anchors.verticalCenter: parent.verticalCenter }
              }
              Row {
                  spacing: 12
                  Text { width: 22; text: "󰞷"; color: "#ffaa00"; font.pixelSize: 18; font.family: "JetBrainsMono Nerd Font"; horizontalAlignment: Text.AlignHCenter; anchors.verticalCenter: parent.verticalCenter }
                  Text { text: "Omarchy (Hyprland)"; color: "#ffffff"; font.pixelSize: 15; font.family: "JetBrainsMono Nerd Font"; font.weight: Font.Bold; anchors.verticalCenter: parent.verticalCenter }
              }

              Item { width: 1; height: 5 } // Spacer
              Rectangle { width: 220; height: 1; color: "#333344"; anchors.horizontalCenter: parent.horizontalCenter } // Divider
              Item { width: 1; height: 5 } // Spacer

              // --- HARDWARE ---
              Text { text: "HARDWARE MONITORS"; color: "#555566"; font.pixelSize: 12; font.family: "JetBrainsMono Nerd Font"; font.weight: Font.Bold; anchors.horizontalCenter: parent.horizontalCenter }

              Row {
                  spacing: 12
                  Text { id: batIcon; width: 22; text: "󰁹"; color: "#00f0ff"; font.pixelSize: 18; font.family: "JetBrainsMono Nerd Font"; horizontalAlignment: Text.AlignHCenter; anchors.verticalCenter: parent.verticalCenter }
                  Text { id: batText; text: "--%"; color: "#ffffff"; font.pixelSize: 15; font.family: "JetBrainsMono Nerd Font"; font.weight: Font.Bold; anchors.verticalCenter: parent.verticalCenter }
              }
              Row {
                  spacing: 12
                  Text { id: ramIcon; width: 22; text: "󰘚"; color: "#7000ff"; font.pixelSize: 18; font.family: "JetBrainsMono Nerd Font"; horizontalAlignment: Text.AlignHCenter; anchors.verticalCenter: parent.verticalCenter }
                  Text { id: ramText; text: "--%"; color: "#ffffff"; font.pixelSize: 15; font.family: "JetBrainsMono Nerd Font"; font.weight: Font.Bold; anchors.verticalCenter: parent.verticalCenter }
              }
              Row {
                  spacing: 12
                  Text { id: cpuIcon; width: 22; text: "󰏈"; color: "#ff007f"; font.pixelSize: 18; font.family: "JetBrainsMono Nerd Font"; horizontalAlignment: Text.AlignHCenter; anchors.verticalCenter: parent.verticalCenter }
                  Text { id: cpuText; text: "--°C"; color: "#ffffff"; font.pixelSize: 15; font.family: "JetBrainsMono Nerd Font"; font.weight: Font.Bold; anchors.verticalCenter: parent.verticalCenter }
              }
          }

          Timer {
              id: hwTimer
              interval: 5000; running: true; repeat: true
              Component.onCompleted: hwTimer.triggered()
              onTriggered: {
                  try {
                      var xhrCap = new XMLHttpRequest();
                      xhrCap.open("GET", "file:///sys/class/power_supply/BAT0/capacity", false);
                      xhrCap.send();
                      var cap = parseInt(xhrCap.responseText.trim());
                      var xhrStat = new XMLHttpRequest();
                      xhrStat.open("GET", "file:///sys/class/power_supply/BAT0/status", false);
                      xhrStat.send();
                      var stat = xhrStat.responseText.trim();
                      if (!isNaN(cap)) {
                          batText.text = cap + "%";
                          if (stat === "Charging") {
                              batIcon.text = "󰂄"; batIcon.color = "#00ffcc";
                          } else {
                              if (cap > 90) batIcon.text = "󰁹";
                              else if (cap > 80) batIcon.text = "󰂂";
                              else if (cap > 60) batIcon.text = "󰁿";
                              else if (cap > 40) batIcon.text = "󰁽";
                              else if (cap > 20) batIcon.text = "󰁻";
                              else { batIcon.text = "󰂃"; batIcon.color = "#ff007f"; }
                              if (cap > 20) batIcon.color = "#00f0ff";
                          }
                      }
                  } catch(e) {}
                  
                  try {
                      var xhrTemp = new XMLHttpRequest();
                      xhrTemp.open("GET", "file:///sys/class/thermal/thermal_zone0/temp", false);
                      xhrTemp.send();
                      var temp = parseInt(xhrTemp.responseText.trim()) / 1000;
                      if (!isNaN(temp)) {
                          cpuText.text = Math.round(temp) + "°C";
                          cpuIcon.color = temp > 80 ? "#ff0000" : (temp > 60 ? "#ffaa00" : "#ff007f");
                      }
                  } catch(e) {}
                  
                  try {
                      var xhrMem = new XMLHttpRequest();
                      xhrMem.open("GET", "file:///proc/meminfo", false);
                      xhrMem.send();
                      var lines = xhrMem.responseText.split('\n');
                      var mTotal = 0;
                      var mAvail = 0;
                      for (var i = 0; i < lines.length; i++) {
                          if (lines[i].indexOf("MemTotal:") === 0) {
                              mTotal = parseInt(lines[i].replace(/[^0-9]/g, ''));
                          } else if (lines[i].indexOf("MemAvailable:") === 0) {
                              mAvail = parseInt(lines[i].replace(/[^0-9]/g, ''));
                          }
                      }
                      if (mTotal > 0 && mAvail > 0) {
                          var mUsed = mTotal - mAvail;
                          var mPercent = Math.round((mUsed / mTotal) * 100);
                          ramText.text = mPercent + "%";
                          ramIcon.color = mPercent > 90 ? "#ff0000" : (mPercent > 70 ? "#ffaa00" : "#7000ff");
                      }
                  } catch(e) {}
              }
          }
      }
  }

  // ==========================================
  // CENTER: LOGIN HUD
  // ==========================================
  Column {
      anchors.centerIn: parent
      spacing: 60

      // Logo Effect
      Item {
          width: 500; height: 120
          anchors.horizontalCenter: parent.horizontalCenter
          
          Text {
              text: "X64 LIOS"
              color: "#ff007f"; font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 85; font.weight: Font.Black; font.letterSpacing: 15
              anchors.centerIn: parent; anchors.horizontalCenterOffset: -4; anchors.verticalCenterOffset: 3; opacity: 0.8
          }
          Text {
              text: "X64 LIOS"
              color: "#00f0ff"; font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 85; font.weight: Font.Black; font.letterSpacing: 15
              anchors.centerIn: parent; anchors.horizontalCenterOffset: 4; anchors.verticalCenterOffset: -3; opacity: 0.8
          }
          Text {
              text: "X64 LIOS"
              color: "#ffffff"; font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 85; font.weight: Font.Black; font.letterSpacing: 15
              anchors.centerIn: parent
          }
          Rectangle {
              width: 120; height: 4; color: "#00ffcc"
              anchors.bottom: parent.bottom; anchors.horizontalCenter: parent.horizontalCenter
              SequentialAnimation on opacity {
                  loops: Animation.Infinite
                  NumberAnimation { to: 0.2; duration: 1500; easing.type: Easing.InOutSine }
                  NumberAnimation { to: 1.0; duration: 1500; easing.type: Easing.InOutSine }
              }
          }
      }

      // User Selector
      Column {
          spacing: 15
          anchors.horizontalCenter: parent.horizontalCenter

          Text {
              text: "S Y S T E M   O P E R A T O R"
              color: "#666677"; font.pixelSize: 11; font.family: "JetBrainsMono Nerd Font"; font.weight: Font.Bold; font.capitalization: Font.AllUppercase; font.letterSpacing: 2
              anchors.horizontalCenter: parent.horizontalCenter
          }

          Row {
              anchors.horizontalCenter: parent.horizontalCenter
              spacing: 30
              Text {
                  text: "❮"
                  color: userLeftMouse.containsMouse ? "#00f0ff" : (userModel.rowCount() > 1 ? "#888899" : "#333344")
                  font.pixelSize: 22; font.weight: Font.Black
                  anchors.verticalCenter: parent.verticalCenter
                  MouseArea {
                      id: userLeftMouse
                      anchors.fill: parent; anchors.margins: -10; enabled: userModel.rowCount() > 1; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                      onClicked: root.userIndex = (root.userIndex - 1 + userModel.rowCount()) % userModel.rowCount()
                  }
              }
              Text {
                  text: root.currentUser; font.capitalization: Font.AllUppercase
                  color: "#ffffff"; font.pixelSize: 28; font.family: "JetBrainsMono Nerd Font"; font.weight: Font.Black; font.letterSpacing: 4
                  anchors.verticalCenter: parent.verticalCenter
              }
              Text {
                  text: "❯"
                  color: userRightMouse.containsMouse ? "#00f0ff" : (userModel.rowCount() > 1 ? "#888899" : "#333344")
                  font.pixelSize: 22; font.weight: Font.Black
                  anchors.verticalCenter: parent.verticalCenter
                  MouseArea {
                      id: userRightMouse
                      anchors.fill: parent; anchors.margins: -10; enabled: userModel.rowCount() > 1; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                      onClicked: root.userIndex = (root.userIndex + 1) % userModel.rowCount()
                  }
              }
          }
      }

      // Password Box
      Rectangle {
          id: box
          width: 340; height: 60; color: "#0a0a10"; radius: 30; border.width: 2
          anchors.horizontalCenter: parent.horizontalCenter
          opacity: 0.9

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
              anchors.fill: parent; horizontalAlignment: TextInput.AlignHCenter; verticalAlignment: TextInput.AlignVCenter
              echoMode: TextInput.Password; font.pixelSize: 24; color: "#ffffff"; passwordCharacter: "■"; focus: true
              
              Text {
                  anchors.centerIn: parent; text: "ACCESS CODE"; color: "#555566"; font.pixelSize: 13; font.letterSpacing: 3; font.family: "JetBrainsMono Nerd Font"; font.weight: Font.Bold
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
  // ==========================================
  // BOTTOM LEFT: SESSION SELECTOR (Pill)
  // ==========================================
  Rectangle {
      width: 280; height: 42
      color: "#0a0a10"
      border.color: "#333344"
      border.width: 1
      radius: 21
      opacity: 0.85
      anchors.bottom: parent.bottom
      anchors.left: parent.left
      anchors.margins: 40

      Row {
          anchors.centerIn: parent
          spacing: 20

          Text {
              text: "❮"
              color: sLeftMouse.containsMouse ? "#00f0ff" : "#888899"
              font.pixelSize: 14; font.weight: Font.Black
              MouseArea {
                  id: sLeftMouse; anchors.fill: parent; anchors.margins: -10
                  hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                  onClicked: if (sessionModel.rowCount() > 0) root.currentSessionIndex = (root.currentSessionIndex - 1 + sessionModel.rowCount()) % sessionModel.rowCount()
              }
          }

          Row {
              spacing: 8; anchors.verticalCenter: parent.verticalCenter
              Text { text: "󰇄"; color: "#00f0ff"; font.pixelSize: 15; font.family: "JetBrainsMono Nerd Font"; anchors.verticalCenter: parent.verticalCenter }
              Text {
                  text: {
                      if (typeof sessionModel === "undefined" || sessionModel.rowCount() === 0) return "X64 DESKTOP";
                      var name = sessionModel.data(sessionModel.index(root.currentSessionIndex, 0), 0); // Qt.DisplayRole
                      if (!name || name === "") name = sessionModel.data(sessionModel.index(root.currentSessionIndex, 0), sessionModel.NameRole);
                      if (!name || name === "") name = sessionModel.data(sessionModel.index(root.currentSessionIndex, 0), sessionModel.NameRole);
                      return (name && name !== "") ? name : "X64 DESKTOP";
                  }
                  color: "#ffffff"; font.pixelSize: 13; font.family: "JetBrainsMono Nerd Font"; font.weight: Font.Bold; font.capitalization: Font.AllUppercase; font.letterSpacing: 1
                  anchors.verticalCenter: parent.verticalCenter
              }
          }

          Text {
              text: "❯"
              color: sRightMouse.containsMouse ? "#00f0ff" : "#888899"
              font.pixelSize: 14; font.weight: Font.Black
              MouseArea {
                  id: sRightMouse; anchors.fill: parent; anchors.margins: -10
                  hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                  onClicked: if (sessionModel.rowCount() > 0) root.currentSessionIndex = (root.currentSessionIndex + 1) % sessionModel.rowCount()
              }
          }
      }
  }

  // BOTTOM RIGHT: POWER CONTROLS
  // ==========================================
  Row {
      anchors.bottom: parent.bottom
      anchors.right: parent.right
      anchors.margins: 40
      spacing: 15

      Rectangle {
          width: 130; height: 42; radius: 21; border.width: 1
          color: rebootMouse.containsMouse ? "#112233" : "#0a0a10"
          border.color: rebootMouse.containsMouse ? "#00f0ff" : "#333344"
          opacity: 0.85
          Row {
              anchors.centerIn: parent; spacing: 8
              Text { text: "󰜉"; color: rebootMouse.containsMouse ? "#00f0ff" : "#aaaaaa"; font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 14 }
              Text { text: "REBOOT"; color: rebootMouse.containsMouse ? "#00f0ff" : "#aaaaaa"; font.pixelSize: 12; font.family: "JetBrainsMono Nerd Font"; font.weight: Font.Bold; font.capitalization: Font.AllUppercase; font.letterSpacing: 1 }
          }
          MouseArea { id: rebootMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: sddm.reboot() }
      }

      Rectangle {
          width: 140; height: 42; radius: 21; border.width: 1
          color: powerMouse.containsMouse ? "#331111" : "#0a0a10"
          border.color: powerMouse.containsMouse ? "#ff007f" : "#333344"
          opacity: 0.85
          Row {
              anchors.centerIn: parent; spacing: 8
              Text { text: "󰐥"; color: powerMouse.containsMouse ? "#ff007f" : "#aaaaaa"; font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 14 }
              Text { text: "SHUTDOWN"; color: powerMouse.containsMouse ? "#ff007f" : "#aaaaaa"; font.pixelSize: 12; font.family: "JetBrainsMono Nerd Font"; font.weight: Font.Bold; font.capitalization: Font.AllUppercase; font.letterSpacing: 1 }
          }
          MouseArea { id: powerMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: sddm.powerOff() }
      }
  }

  Component.onCompleted: password.forceActiveFocus()
}
