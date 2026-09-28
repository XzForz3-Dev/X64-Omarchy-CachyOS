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
    root.targetScreen = Quickshell.screens[0]
    
    // Cargar lista de temas
    backendProcess.currentAction = "list"
    backendProcess.command = ["python3", Quickshell.env("OMARCHY_PATH") + "/bin/x64-theme-creator-backend", "list"]
    backendProcess.running = true
  }

  function close() {
    root.shown = false
    shell.closePluginOverlay("x64.theme-creator")
  }

  // Interacción con el script backend
  Process {
    id: backendProcess
    property string currentAction: ""
    stdout: StdioCollector {
      id: backendOut
      waitForEnd: true
    }
    stderr: StdioCollector {
      id: backendErr
      waitForEnd: true
    }
    
    onExited: {
      if (exitCode === 0) {
        try {
          var res = JSON.parse(backendOut.text)
          if (res.status === "success") {
            if (currentAction === "save") {
              statusText.text = res.message
              statusText.color = "#00ff55"
            } else if (currentAction === "read") {
              accentInput.text = res.data.accent
              bgInput.text = res.data.background
              fgInput.text = res.data.foreground
              statusText.text = "Tema cargado correctamente."
              statusText.color = "#00ff55"
            } else if (currentAction === "list") {
              themeDropdown.options = res.themes || []
              statusText.text = "Lista de temas actualizada."
              statusText.color = "#00ff55"
            }
          } else {
            statusText.text = res.message || "Error desconocido"
            statusText.color = "#ff5555"
          }
        } catch(e) {
          statusText.text = "Error al procesar respuesta"
          statusText.color = "#ff5555"
        }
      } else {
        statusText.text = "Error de ejecución: " + backendErr.text
        statusText.color = "#ff5555"
      }
    }
  }

  function saveTheme() {
    if (nameInput.text.trim() === "") {
      statusText.text = "Error: Escribe un nombre para el tema"
      statusText.color = "#ff5555"
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
    // No cerrar al hacer clic afuera
  }

  Rectangle {
    anchors.centerIn: parent
    width: 450
    height: layout.implicitHeight + 40
    color: Color.background
    radius: Style.cornerRadius
    border.color: Color.accent
    border.width: 2
    
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

      RowLayout {
        Layout.fillWidth: true
        Layout.bottomMargin: 5

        Item {
          Layout.fillWidth: true
        }

        Text {
          text: "X64 Theme Creator"
          color: Color.foreground
          font.pixelSize: 24
          font.bold: true
          Layout.alignment: Qt.AlignHCenter
        }

        Item {
          Layout.fillWidth: true
        }

        Ui.Button {
          text: "✕"
          onClicked: root.close()
          Layout.alignment: Qt.AlignRight
        }
      }
      
      RowLayout {
        Layout.fillWidth: true
        spacing: 10
        Text { text: "Temas\nExistentes:"; color: Color.foreground; Layout.preferredWidth: 80 }
        Ui.SearchableDropdown {
          id: themeDropdown
          Layout.fillWidth: true
          placeholderText: "Selecciona un tema para editarlo..."
          onChanged: function(val) {
            nameInput.text = val;
            loadTheme();
          }
        }
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
          border.color: Color.accent
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
          border.color: Color.accent
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
          border.color: Color.accent
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
          text: "Guardar Tema"
          onClicked: saveTheme()
        }
      }
    }
  }
}
