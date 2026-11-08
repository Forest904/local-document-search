import QtQuick

QtObject {
    property bool dark: false
    readonly property color backdrop: dark ? "#191D1B" : "#FAF9F6"
    readonly property color surface: dark ? "#242A26" : "#FFFFFF"
    readonly property color ink: dark ? "#EDF1ED" : "#252826"
    readonly property color muted: dark ? "#B5BFB7" : "#606861"
    readonly property color accent: dark ? "#ACD5BC" : "#315D50"
    readonly property color sage: dark ? "#30463A" : "#DFEAE2"
    readonly property color lavender: dark ? "#3C354B" : "#E9E5F3"
    readonly property color line: dark ? "#48534B" : "#CDD5CE"
    readonly property color error: dark ? "#F3BEAC" : "#923B28"
    readonly property int radius: 16
}
