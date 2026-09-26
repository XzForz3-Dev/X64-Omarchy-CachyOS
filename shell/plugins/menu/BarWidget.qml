import QtQuick
import qs.Ui
import Quickshell

BarWidget {
  id: root
  moduleName: "omarchy.menu"

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: ""
    hasVisualContent: true
    horizontalMargin: 7.5

    Image {
      anchors.centerIn: parent
      source: "file://" + Quickshell.env("OMARCHY_PATH") + "/shell/assets/x64-logo.svg"
      width: Math.floor(button.height * 0.5)
      height: width
      sourceSize: Qt.size(width, height)
      fillMode: Image.PreserveAspectFit
      antialiasing: true
      mipmap: true
    }

    onPressed: function(mouseButton) {
      if (!root.bar) return
      if (mouseButton === Qt.RightButton) root.bar.run("xdg-terminal-exec")
      else root.bar.run("omarchy-shell shell toggle omarchy.menu '{\"menu\":\"root\"}'")
    }
  }
}
