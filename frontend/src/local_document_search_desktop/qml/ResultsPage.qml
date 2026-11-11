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
    function focusResult() {
        results.currentIndex = page.v.resultsIndex;
        results.forceActiveFocus();
    }
    spacing: height < 500 ? 8 : 16
    SearchBox {
        id: search
        theme: page.theme
        Layout.fillWidth: true
    }
    FilterSummary {
        theme: page.theme
        Layout.fillWidth: true
    }
    RowLayout {
        objectName: "spellingProposal"
        visible: page.v.spellingProposal !== ""
        Layout.fillWidth: true
        spacing: 4
        Label {
            text: desktop.labels.didYouMean + ":"
            color: page.theme.muted
            Layout.alignment: Qt.AlignTop
            Layout.maximumWidth: page.width * 0.3
            wrapMode: Text.Wrap
        }
        Button {
            objectName: "acceptSpelling"
            text: page.v.spellingProposal
            Accessible.name: desktop.labels.searchCorrection + ": " + page.v.spellingProposal
            enabled: page.v.searchable
            hoverEnabled: true
            activeFocusOnTab: true
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            implicitHeight: contentItem.implicitHeight + 4
            padding: 2
            background: Rectangle {
                color: "transparent"
                radius: 4
                border.width: parent.activeFocus ? 2 : 0
                border.color: page.theme.accent
            }
            contentItem: Text {
                text: parent.text
                color: parent.hovered ? page.theme.accent : page.theme.ink
                font.weight: Font.DemiBold
                font.underline: parent.hovered || parent.activeFocus
                wrapMode: Text.Wrap
                textFormat: Text.PlainText
            }
            onClicked: desktop.acceptSpelling()
        }
    }
    Label {
        objectName: "resultsSummary"
        text: page.v.searching ? desktop.labels.searching
              : page.v.hasResponse && page.v.searchDuration >= 0
                ? desktop.labels.results + " " + page.v.total + " " + desktop.labels.resultsIn
                  + " " + page.v.searchDuration.toFixed(3).replace(".", page.v.language === "it" ? "," : ".")
                  + " " + desktop.labels.seconds
                : desktop.labels.enter
        color: page.theme.muted
        wrapMode: Text.Wrap
        Layout.fillWidth: true
    }
    ListView {
        id: results
        objectName: "results"
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        spacing: 4
        model: desktop.results
        currentIndex: page.v.resultsIndex
        activeFocusOnTab: true
        Accessible.name: desktop.labels.results
        ScrollBar.vertical: ScrollBar {}
        Component.onCompleted: Qt.callLater(function () { results.contentY = page.v.resultsScroll; })
        Component.onDestruction: desktop.rememberResultsScroll(results.contentY)
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
            visible: results.count === 0 && page.v.hasResponse && !page.v.searching
            text: desktop.labels.empty
            color: page.theme.muted
            elide: Text.ElideRight
            Layout.maximumWidth: Math.max(100, page.width - 120)
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
