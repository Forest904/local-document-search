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
        y: Math.max(8, (parent.height - implicitHeight) * 0.36)
        width: Math.max(0, Math.min(760, parent.width - (parent.width < 700 ? 16 : 64)))
        spacing: parent.height < 500 ? 12 : 24
        Brand {
            theme: page.theme
            large: true
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
        visible: page.height >= 300
        anchors.bottom: parent.bottom
        anchors.bottomMargin: page.height < 500 ? 8 : 24
        anchors.horizontalCenter: parent.horizontalCenter
        text: desktop.labels.local
        color: page.theme.muted
        font.pixelSize: 12
    }
}
