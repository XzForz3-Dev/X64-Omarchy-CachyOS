import QtQuick 2.15
import SddmComponents 2.0

Rectangle {
  id: root
  width: 1920
  height: 1080

  gradient: Gradient {
      GradientStop { position: 0.0; color: "#050508" }
      GradientStop { position: 1.0; color: "#12101c" }
  }

  property int userIndex: userModel.lastIndex >= 0 ? userModel.lastIndex : 0
  property string currentUser: userModel.rowCount() > 0 ? userModel.data(userModel.index(userIndex, 0), userModel.NameRole) : ""

  Connections {
    target: sddm
    function onLoginFailed() { password.text = ""; password.focus = true; box.shake() }
  }

  // Soft background glows
  Rectangle {
      width: 800
      height: 800
      radius: 400
      color: "#ff007f"
      opacity: 0.04
      anchors.centerIn: parent
  }

  Rectangle {
      width: 600
      height: 600
      radius: 300
      color: "#00f0ff"
      opacity: 0.04
      anchors.centerIn: parent
      anchors.verticalCenterOffset: -100
  }

  Column {
      anchors.centerIn: parent
      spacing: 60

      // TEXT-BASED CYBERPUNK LOGO
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
          
          // Pulsing underline
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
          spacing: 10
          anchors.horizontalCenter: parent.horizontalCenter

          Text {
              text: "S Y S T E M   O P E R A T O R"
              color: "#555566"
              font.pixelSize: 12
              font.family: "JetBrainsMono Nerd Font"
              font.weight: Font.Bold
              anchors.horizontalCenter: parent.horizontalCenter
          }

          Text {
              text: root.currentUser.toUpperCase()
              color: "#ffffff"
              font.pixelSize: 26
              font.family: "JetBrainsMono Nerd Font"
              font.weight: Font.Black
              font.letterSpacing: 4
              anchors.horizontalCenter: parent.horizontalCenter
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
                      sddm.login(root.currentUser, password.text, sessionModel.lastIndex)
                      event.accepted = true
                  }
              }
          }
      }
  }
  Component.onCompleted: password.forceActiveFocus()
}
