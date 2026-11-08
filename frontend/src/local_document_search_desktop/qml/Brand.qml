import QtQuick

Item {
    id: brand
    required property var theme
    property bool large: false
    property bool resultsHeader: false
    implicitWidth: large ? 264 : resultsHeader ? 130 : 122
    implicitHeight: large ? 80 : 44
    Accessible.role: Accessible.StaticText
    Accessible.name: "Luma"
    Row {
        anchors.centerIn: parent
        spacing: brand.large ? -20 : brand.resultsHeader ? 2 : -6
        Image {
            width: brand.large ? 64 : 32
            height: width
            anchors.verticalCenter: parent.verticalCenter
            source: "../assets/luma-desktop-original.png"
            sourceSize.width: brand.large ? 128 : 64
            sourceSize.height: brand.large ? 128 : 64
            smooth: true
        }
        Rectangle {
            width: brand.large ? 220 : 96
            height: brand.large ? 80 : 44
            clip: true
            anchors.verticalCenter: parent.verticalCenter
            radius: 8
            color: "transparent"
            Image {
                width: brand.large ? 294 : 126
                height: parent.height
                x: brand.large ? -34 : -14
                source: "../assets/luma-wordmark-" + (brand.theme.dark ? "dark" : "light") + ".png"
                fillMode: Image.PreserveAspectFit
                smooth: true
            }
        }
    }
}
