import QtQuick
import QtQuick.Controls.Basic

Button {
    id: control
    required property var theme
    property bool primary: false
    property string iconName: ""
    activeFocusOnTab: true
    Accessible.name: text !== "" ? text : iconName
    implicitHeight: 44
    implicitWidth: contentItem.implicitWidth + leftPadding + rightPadding
    leftPadding: 20
    rightPadding: 20
    background: Rectangle {
        radius: 12
        color: control.down ? control.theme.lavender : control.hovered || control.primary ? control.theme.sage : control.theme.surface
        border.color: control.activeFocus ? control.theme.accent : control.theme.line
        border.width: control.activeFocus ? 2 : 1
        opacity: control.enabled ? 1 : 0.5
    }
    contentItem: Row {
        spacing: control.iconName ? 8 : 0
        Image {
            visible: control.iconName !== ""
            width: visible ? 20 : 0
            height: 20
            sourceSize.width: 20
            sourceSize.height: 20
            anchors.verticalCenter: parent.verticalCenter
            source: control.iconName ? "../assets/" + control.iconName + "-" + (control.theme.dark ? "dark" : "light") + ".svg" : ""
            opacity: control.enabled ? 1 : 0.5
        }
        Text {
            text: control.text
            font: control.font
            color: control.enabled ? control.theme.ink : control.theme.muted
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}
