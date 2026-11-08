import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

ColumnLayout {
    id: page
    required property var theme
    property var v: desktop.view
    function focusQuery() {
        search.focusQuery();
    }
    spacing: 16
    SearchBox {
        id: search
        theme: page.theme
        Layout.fillWidth: true
    }
    FilterSummary {
        theme: page.theme
        Layout.fillWidth: true
    }
    Label {
        text: page.v.reading ? desktop.labels.searching : page.v.hasResponse ? desktop.labels.results + " \u00b7 " + page.v.total : desktop.labels.enter
        color: page.theme.muted
    }
    ListView {
        id: results
        objectName: "results"
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        spacing: 4
        model: desktop.results
        currentIndex: -1
        activeFocusOnTab: true
        Accessible.name: desktop.labels.results
        ScrollBar.vertical: ScrollBar {}
        Keys.onReturnPressed: if (currentIndex >= 0)
            desktop.openResult(currentIndex)
        delegate: ResultItem {
            theme: page.theme
        }
        Label {
            anchors.centerIn: parent
            width: parent.width - 32
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
            visible: results.count === 0 && page.v.hasResponse && !page.v.reading
            text: desktop.labels.empty
            color: page.theme.muted
        }
    }
    RowLayout {
        ActionButton {
            theme: page.theme
            iconName: "back"
            text: desktop.labels.previous
            enabled: page.v.canPrevious
            onClicked: desktop.page(-1)
        }
        Label {
            text: page.v.hasResponse ? (page.v.total ? String(page.v.offset + 1) + "\u2013" + Math.min(page.v.offset + 50, page.v.total) + " / " + page.v.total : "0") : ""
            color: page.theme.muted
        }
        Item {
            Layout.fillWidth: true
        }
        ActionButton {
            theme: page.theme
            iconName: "next"
            text: desktop.labels.next
            enabled: page.v.canNext
            onClicked: desktop.page(1)
        }
    }
}
