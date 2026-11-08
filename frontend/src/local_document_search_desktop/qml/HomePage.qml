import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Item {
    id: page
    required property var theme
    function focusQuery() {
        search.focusQuery();
    }
    ColumnLayout {
        anchors.horizontalCenter: parent.horizontalCenter
        y: Math.max(24, (parent.height - implicitHeight) * 0.36)
        width: Math.min(760, parent.width - 64)
        spacing: 24
        Brand {
            theme: page.theme
            large: true
            Layout.alignment: Qt.AlignHCenter
        }
        Label {
            text: desktop.labels.discover
            color: page.theme.muted
            font.pixelSize: 20
            Layout.alignment: Qt.AlignHCenter
        }
        SearchBox {
            id: search
            theme: page.theme
            Layout.fillWidth: true
        }
        FilterSummary {
            theme: page.theme
            Layout.fillWidth: true
        }
    }
    Label {
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 24
        anchors.horizontalCenter: parent.horizontalCenter
        text: desktop.labels.local
        color: page.theme.muted
        font.pixelSize: 12
    }
}
