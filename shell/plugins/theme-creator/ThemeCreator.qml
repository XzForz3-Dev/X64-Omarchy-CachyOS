import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import Quickshell.Io
import qs.Commons
import qs.Ui as Ui

Ui.OverlayWindow {
  id: root
  objectName: "x64-theme-creator-overlay"

  function open(payloadJson) {
    root.shown = true
  }

  function close() {
    root.shown = false
    shell.closePluginOverlay("x64.theme-creator")
  }

  // Interacción con el script backend
  Process {
    id: backendProcess
    property string currentAction: ""
    
    onExited: {
      if (exitCode === 0) {
        try {
          var res = JSON.parse(stdout)
          if (res.status === "success") {
            if (currentAction === "save") {
              statusText.text = res.message
              statusText.color = Color.green
            } else if (currentAction === "read") {
              accentInput.text = res.data.accent
              bgInput.text = res.data.background
              fgInput.text = res.data.foreground
              statusText.text = "Tema cargado correctamente."
              statusText.color = Color.green
            }
          } else {
            statusText.text = res.message || "Error desconocido"
            statusText.color = Color.red
          }
        } catch(e) {
          statusText.text = "Error al procesar respuesta"
          statusText.color = Color.red
        }
      } else {
        statusText.text = "Error de ejecución: " + stderr
        statusText.color = Color.red
      }
    }
  }

  function saveTheme() {
    if (nameInput.text.trim() === "") {
      statusText.text = "Error: Escribe un nombre para el tema"
      statusText.color = Color.red
      return
    }
    statusText.text = "Guardando..."
    statusText.color = Color.foreground
    backendProcess.currentAction = "save"
    backendProcess.command = ["python3", Quickshell.env("OMARCHY_PATH") + "/bin/x64-theme-creator-backend", "save", nameInput.text, accentInput.text, fgInput.text, bgInput.text]
    backendProcess.running = true
  }

  function loadTheme() {
    if (nameInput.text.trim() === "") {
      statusText.text = "Error: Escribe el nombre del tema a cargar"
      statusText.color = Color.red
      return
    }
    statusText.text = "Cargando..."
    statusText.color = Color.foreground
    backendProcess.currentAction = "read"
    backendProcess.command = ["python3", Quickshell.env("OMARCHY_PATH") + "/bin/x64-theme-creator-backend", "read", nameInput.text]
    backendProcess.running = true
  }

  MouseArea {
    anchors.fill: parent
    onClicked: root.close()
  }

  Rectangle {
    anchors.centerIn: parent
    width: 450
    height: layout.implicitHeight + 40
    color: Color.popups.surface
    radius: Style.cornerRadius
    border.color: Color.popups.border

    MouseArea {
      anchors.fill: parent
      // Atrapa clics para que no cierren el overlay si se clica dentro
      onClicked: {}
    }

    ColumnLayout {
      id: layout
      anchors.left: parent.left
      anchors.right: parent.right
      anchors.verticalCenter: parent.verticalCenter
      anchors.margins: 20
      spacing: 15

      Text {
        text: "X64 Theme Creator"
        color: Color.foreground
        font.pixelSize: 24
        font.bold: true
        Layout.alignment: Qt.AlignHCenter
        Layout.bottomMargin: 10
      }

      RowLayout {
        Layout.fillWidth: true
        spacing: 10
        Text { text: "Nombre:"; color: Color.foreground; Layout.preferredWidth: 80 }
        Ui.TextField {
          id: nameInput
          Layout.fillWidth: true
          placeholderText: "Ej. Goku, Vaporwave..."
        }
      }

      RowLayout {
        Layout.fillWidth: true
        spacing: 10
        Text { text: "Acento:"; color: Color.foreground; Layout.preferredWidth: 80 }
        Ui.TextField {
          id: accentInput
          Layout.fillWidth: true
          placeholderText: "#ffaa00"
          text: "#00ccff"
        }
        Rectangle {
          width: 24; height: 24; radius: 12
          color: accentInput.text.length >= 4 ? accentInput.text : "transparent"
          border.color: Color.border
        }
      }

      RowLayout {
        Layout.fillWidth: true
        spacing: 10
        Text { text: "Fondo:"; color: Color.foreground; Layout.preferredWidth: 80 }
        Ui.TextField {
          id: bgInput
          Layout.fillWidth: true
          placeholderText: "#000000"
          text: "#0a0a0f"
        }
        Rectangle {
          width: 24; height: 24; radius: 12
          color: bgInput.text.length >= 4 ? bgInput.text : "transparent"
          border.color: Color.border
        }
      }

      RowLayout {
        Layout.fillWidth: true
        spacing: 10
        Text { text: "Texto (FG):"; color: Color.foreground; Layout.preferredWidth: 80 }
        Ui.TextField {
          id: fgInput
          Layout.fillWidth: true
          placeholderText: "#ffffff"
          text: "#e0e0e0"
        }
        Rectangle {
          width: 24; height: 24; radius: 12
          color: fgInput.text.length >= 4 ? fgInput.text : "transparent"
          border.color: Color.border
        }
      }

      Text {
        id: statusText
        text: "Listo. Crea o edita un tema."
        color: Color.muted
        font.pixelSize: 12
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: 5
      }

      RowLayout {
        Layout.fillWidth: true
        Layout.topMargin: 10
        spacing: 15

        Ui.Button {
          Layout.fillWidth: true
          text: "Cargar Existente"
          onClicked: loadTheme()
        }

        Ui.Button {
          Layout.fillWidth: true
          text: "Guardar Tema"
          onClicked: saveTheme()
        }
      }
    }
  }
}
