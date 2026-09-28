import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Window
import QtQuick.Dialogs

ApplicationWindow {
  id: root
  title: "X64 Theme Creator"
  width: 450
  height: 520
  visible: true
  color: SysTheme.background

  Component.onCompleted: {
      Backend.listThemes()
  }

  Connections {
      target: Backend
      function onThemeLoaded(data) {
          accentInput.text = data.accent || ""
          bgInput.text = data.background || ""
          fgInput.text = data.foreground || ""
      }
      function onThemesListed(themes) {
          themeModel.clear()
          for (var i = 0; i < themes.length; i++) {
              themeModel.append({ text: themes[i] })
          }
      }
      function onStatusUpdated(msg, color) {
          statusText.text = msg
          statusText.color = color
      }
  }

  FileDialog {
    id: fileDialog
    title: "Selecciona una imagen para extraer colores"
    nameFilters: ["Imágenes (*.png *.jpg *.jpeg *.webp)"]
    onAccepted: {
      imgInput.text = fileDialog.selectedFile.toString().replace("file://", "");
      Backend.extractColors(imgInput.text);
    }
  }

  ColumnLayout {
      anchors.fill: parent
      anchors.margins: 20
      spacing: 15

      Text {
          text: "X64 Theme Creator"
          color: SysTheme.foreground
          font.pixelSize: 24
          font.bold: true
          Layout.alignment: Qt.AlignHCenter
          Layout.bottomMargin: 10
      }

      RowLayout {
          Layout.fillWidth: true
          spacing: 10
          Text { text: "Temas\nExistentes:"; color: SysTheme.foreground; Layout.preferredWidth: 80 }
          
          ComboBox {
              id: themeDropdown
              Layout.fillWidth: true
              model: ListModel { id: themeModel }
              onActivated: {
                  nameInput.text = currentText
                  Backend.loadTheme(currentText)
              }
          }
      }

      RowLayout {
          Layout.fillWidth: true
          spacing: 10
          Text { text: "Desde\nImagen:"; color: SysTheme.foreground; Layout.preferredWidth: 80 }
          TextField {
              id: imgInput
              Layout.fillWidth: true
              placeholderText: "Ruta de la imagen"
              color: SysTheme.foreground
              background: Rectangle { color: "#222"; border.color: SysTheme.muted }
          }
          Button {
              text: "📁"
              onClicked: fileDialog.open()
          }
          Button {
              text: "Extraer"
              onClicked: Backend.extractColors(imgInput.text)
          }
      }
      
      Rectangle {
          Layout.fillWidth: true
          height: 1
          color: SysTheme.muted
          opacity: 0.3
      }

      RowLayout {
          Layout.fillWidth: true
          spacing: 10
          Text { text: "Guardar\nComo:"; color: SysTheme.foreground; Layout.preferredWidth: 80 }
          TextField {
              id: nameInput
              Layout.fillWidth: true
              placeholderText: "Nombre de tu tema"
              color: SysTheme.foreground
              background: Rectangle { color: "#222"; border.color: SysTheme.muted }
          }
      }

      RowLayout {
          Layout.fillWidth: true
          spacing: 10
          Text { text: "Acento:"; color: SysTheme.foreground; Layout.preferredWidth: 80 }
          TextField {
              id: accentInput
              Layout.fillWidth: true
              text: "#00ccff"
              color: SysTheme.foreground
              background: Rectangle { color: "#222"; border.color: SysTheme.muted }
          }
          Rectangle {
              width: 24; height: 24; radius: 12
              color: accentInput.text.length >= 4 ? accentInput.text : "transparent"
              border.color: SysTheme.accent
          }
      }

      RowLayout {
          Layout.fillWidth: true
          spacing: 10
          Text { text: "Fondo:"; color: SysTheme.foreground; Layout.preferredWidth: 80 }
          TextField {
              id: bgInput
              Layout.fillWidth: true
              text: "#0a0a0f"
              color: SysTheme.foreground
              background: Rectangle { color: "#222"; border.color: SysTheme.muted }
          }
          Rectangle {
              width: 24; height: 24; radius: 12
              color: bgInput.text.length >= 4 ? bgInput.text : "transparent"
              border.color: SysTheme.accent
          }
      }

      RowLayout {
          Layout.fillWidth: true
          spacing: 10
          Text { text: "Texto (FG):"; color: SysTheme.foreground; Layout.preferredWidth: 80 }
          TextField {
              id: fgInput
              Layout.fillWidth: true
              text: "#e0e0e0"
              color: SysTheme.foreground
              background: Rectangle { color: "#222"; border.color: SysTheme.muted }
          }
          Rectangle {
              width: 24; height: 24; radius: 12
              color: fgInput.text.length >= 4 ? fgInput.text : "transparent"
              border.color: SysTheme.accent
          }
      }

      Text {
          id: statusText
          text: "Listo. Crea, edita o extrae desde imagen."
          color: SysTheme.muted
          font.pixelSize: 12
          Layout.alignment: Qt.AlignHCenter
          wrapMode: Text.Wrap
          Layout.maximumWidth: 400
      }

      Item { Layout.fillHeight: true } // Spacer

      Button {
          Layout.fillWidth: true
          text: "Guardar Tema"
          onClicked: Backend.saveTheme(nameInput.text, accentInput.text, fgInput.text, bgInput.text)
          background: Rectangle { color: SysTheme.accent; radius: 4 }
          contentItem: Text { text: parent.text; color: SysTheme.background; horizontalAlignment: Text.AlignHCenter }
      }
  }
}
