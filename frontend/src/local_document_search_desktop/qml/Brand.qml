import QtQuick
import QtQuick.Controls.Basic

Button {
    id: brand
    required property var theme
    property bool large: false
    text: "Luma"
    Accessible.name: "Luma \u2014 " + desktop.labels.home
    implicitWidth: large ? 220 : 112
    implicitHeight: large ? 80 : 44
    background: Rectangle {
        color: "transparent"
        radius: 12
        border.color: brand.activeFocus ? brand.theme.accent : "transparent"
    }
    contentItem: Row {
        spacing: brand.large ? 16 : 8
        Image {
            width: brand.large ? 64 : 32
            height: width
            anchors.verticalCenter: parent.verticalCenter
            source: "../assets/luma-desktop-original.png"
            sourceSize.width: brand.large ? 128 : 64
            sourceSize.height: brand.large ? 128 : 64
            smooth: true
        }
        Text {
            text: "Luma"
            color: brand.theme.ink
            font.family: "Segoe UI"
            font.pixelSize: brand.large ? 56 : 28
            font.weight: Font.DemiBold
            anchors.verticalCenter: parent.verticalCenter
        }
    }
    onClicked: desktop.navigate("home")
}
