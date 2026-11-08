import QtQuick
import QtQuick.Controls.Basic

ComboBox {
    id: control
    required property var theme
    implicitHeight: 44
    leftPadding: 16
    rightPadding: 40
    background: Rectangle {
        radius: 12
        color: control.theme.surface
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? control.theme.accent : control.theme.line
    }
    contentItem: Text {
        text: control.displayText
        font: control.font
        color: control.theme.ink
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    indicator: Text {
        x: control.width - 30
        y: (control.height - height) / 2
        text: "\u2304"
        font.pixelSize: 20
        color: control.theme.muted
    }
    delegate: ItemDelegate {
        required property int index
        required property string modelData
        width: control.popup.availableWidth
        text: modelData
        highlighted: control.highlightedIndex === index
        palette.text: control.theme.ink
        palette.buttonText: control.theme.ink
        palette.highlightedText: control.theme.ink
        background: Rectangle {
            radius: 8
            color: parent.highlighted || parent.hovered ? control.theme.sage : control.theme.surface
        }
    }
    popup: Popup {
        y: control.height + 4
        width: control.width
        padding: 4
        background: Rectangle {
            color: control.theme.surface
            radius: 12
            border.color: control.theme.line
        }
        contentItem: ListView {
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            clip: true
        }
    }
}
