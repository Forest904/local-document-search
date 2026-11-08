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
    ActionButton {
        theme: summary.theme
        text: desktop.labels.settings
        onClicked: desktop.navigate("settings")
    }
    ActionButton {
        theme: summary.theme
        text: desktop.labels.resetFilters
        onClicked: desktop.resetOptions()
    }
}
