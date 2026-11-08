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
        objectName: "resultsSummary"
        text: page.v.reading ? desktop.labels.searching
              : page.v.hasResponse && page.v.searchDuration >= 0
                ? desktop.labels.results + " " + page.v.total + " " + desktop.labels.resultsIn
                  + " " + page.v.searchDuration.toFixed(3).replace(".", page.v.language === "it" ? "," : ".")
                  + " " + desktop.labels.seconds
                : desktop.labels.enter
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
        objectName: "pagination"
        visible: page.v.hasResponse && page.v.total > page.v.pageSize
        Layout.alignment: Qt.AlignHCenter
        spacing: 12
        ActionButton {
            objectName: "previousPage"
            theme: page.theme
            iconName: "back"
            text: ""
            Accessible.name: desktop.labels.previous
            leftPadding: 12
            rightPadding: 12
            enabled: page.v.canPrevious
            onClicked: desktop.page(-1)
        }
        Label {
            objectName: "pageSummary"
            text: desktop.labels.page + " " + (Math.floor(page.v.offset / page.v.pageSize) + 1)
                  + " \u00b7 " + desktop.labels.results + " " + (page.v.offset + 1)
                  + "\u2013" + Math.min(page.v.offset + page.v.pageSize, page.v.total)
                  + " / " + page.v.total
            color: page.theme.muted
        }
        ActionButton {
            objectName: "nextPage"
            theme: page.theme
            iconName: "next"
            text: ""
            Accessible.name: desktop.labels.next
            leftPadding: 12
            rightPadding: 12
            enabled: page.v.canNext
            onClicked: desktop.page(1)
        }
    }
}
