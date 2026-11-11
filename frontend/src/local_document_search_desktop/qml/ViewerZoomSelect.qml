import QtQuick
import QtQuick.Controls.Basic

ComboBox {
    id: control
    required property var theme
    implicitHeight: 36
    leftPadding: 16
    rightPadding: 36
    palette.text: theme.ink
    palette.highlightedText: theme.ink
    background: Rectangle {
        radius: 18
        color: !control.enabled ? control.theme.surface : control.down || control.popup.visible ? control.theme.sage
             : control.hovered ? control.theme.sage : control.theme.lavender
        border.color: control.activeFocus ? control.theme.accent : control.theme.line
        border.width: control.activeFocus ? 2 : 1
        opacity: control.enabled ? 1 : 0.65
    }
    contentItem: Text {
        text: control.displayText
        color: control.enabled ? control.theme.ink : control.theme.muted
        font.family: control.font.family
        font.pixelSize: 14
        font.weight: Font.DemiBold
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    indicator: Image {
        x: control.width - 30
        y: (control.height - height) / 2
        source: "../assets/next-" + (control.theme.dark ? "dark" : "light") + ".svg"
        sourceSize.width: 16
        sourceSize.height: 16
        rotation: 90
        opacity: control.enabled ? 1 : 0.5
    }
    delegate: ItemDelegate {
        id: option
        objectName: "pdfZoomOption"
        required property int index
        required property string modelData
        width: control.popup.availableWidth
        implicitHeight: 36
        highlighted: control.highlightedIndex === index
        contentItem: Text {
            objectName: "pdfZoomOptionText"
            text: option.modelData
            color: option.enabled ? control.theme.ink : control.theme.muted
            font.family: control.font.family
            font.pixelSize: 14
            font.weight: option.index === control.currentIndex && control.displayText === option.modelData
                         ? Font.DemiBold : Font.Normal
            verticalAlignment: Text.AlignVCenter
            leftPadding: 14
        }
        background: Rectangle {
            radius: 8
            color: option.down ? control.theme.sage
                 : option.highlighted || option.hovered ? control.theme.sage
                 : option.index === control.currentIndex && control.displayText === option.modelData
                   ? control.theme.lavender : control.theme.surface
            border.color: option.activeFocus ? control.theme.accent : "transparent"
            border.width: option.activeFocus ? 2 : 0
        }
    }
    popup: Popup {
        objectName: "pdfZoomPopup"
        y: control.height + 5
        width: control.width
        padding: 5
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
