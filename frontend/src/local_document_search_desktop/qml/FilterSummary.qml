import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

RowLayout {
    id: summary
    required property var theme
    visible: desktop.view.restricted
    Label {
        text: desktop.labels.filters + ": " + desktop.view.optionsSummary
        textFormat: Text.PlainText
        color: summary.theme.muted
        elide: Text.ElideMiddle
        Layout.fillWidth: true
    }
    Button {
        id: clearFilters
        objectName: "clearFilters"
        Layout.preferredWidth: 36
        Layout.preferredHeight: 36
        activeFocusOnTab: true
        Accessible.name: desktop.labels.resetFilters
        ToolTip.visible: hovered
        ToolTip.text: desktop.labels.resetFilters
        background: Rectangle {
            radius: 18
            color: clearFilters.down ? summary.theme.lavender
                   : clearFilters.hovered ? summary.theme.sage : "transparent"
            border.color: clearFilters.activeFocus ? summary.theme.accent : "transparent"
            border.width: clearFilters.activeFocus ? 2 : 0
        }
        contentItem: Label {
            text: "\u00d7"
            font.pixelSize: 23
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            color: summary.theme.muted
        }
        onClicked: desktop.resetOptions()
    }
}
