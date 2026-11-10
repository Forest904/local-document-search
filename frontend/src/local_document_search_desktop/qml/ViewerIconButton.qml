import QtQuick
import QtQuick.Controls.Basic

Button {
    id: control
    required property var theme
    required property string label
    required property string iconName
    property bool rotated: false
    text: label
    Accessible.name: label
    activeFocusOnTab: true
    implicitWidth: 32
    implicitHeight: 32
    padding: 0
    background: Rectangle {
        radius: 8
        color: control.down ? control.theme.lavender : control.hovered ? control.theme.sage : control.theme.surface
        border.color: control.activeFocus ? control.theme.accent : control.theme.line
        border.width: control.activeFocus ? 2 : 1
        opacity: control.enabled ? 1 : 0.5
    }
    contentItem: Image {
        source: "../assets/" + control.iconName + "-" + (control.theme.dark ? "dark" : "light") + ".svg"
        sourceSize.width: 16
        sourceSize.height: 16
        fillMode: Image.PreserveAspectFit
        rotation: control.rotated ? 180 : 0
        opacity: control.enabled ? 1 : 0.5
    }
    ToolTip.visible: hovered
    ToolTip.text: label
    ToolTip.delay: 450
}
