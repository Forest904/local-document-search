import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

ColumnLayout {
    id: box
    required property var theme
    property var v: desktop.view
    property var t: desktop.labels
    function submit() {
        desktop.editQuery(query.text, query.cursorPosition);
        if (box.v.screen === "results" && query.text.trim() === "") {
            desktop.navigate("home");
            return;
        }
        desktop.search();
    }
    function focusQuery() {
        query.forceActiveFocus();
        query.selectAll();
    }
    spacing: 8
    TextField {
        id: query
        objectName: "query"
        Layout.fillWidth: true
        implicitHeight: 56
        leftPadding: 24
        rightPadding: 72
        font.pixelSize: 17
        color: box.theme.ink
        placeholderTextColor: box.theme.muted
        placeholderText: box.t.query
        text: box.v.query
        Accessible.name: box.t.search
        enabled: box.v.searchable
        selectByMouse: true
        background: Rectangle {
            radius: 28
            color: box.theme.surface
            border.color: query.activeFocus ? box.theme.accent : box.theme.line
            border.width: query.activeFocus ? 2 : 1
        }
        onTextEdited: desktop.editQuery(text, cursorPosition)
        onCursorPositionChanged: Qt.callLater(function () {
            if (query.activeFocus)
                desktop.editQuery(query.text, query.cursorPosition);
        })
        onAccepted: box.submit()
        Keys.onDownPressed: if (suggestions.count) {
            suggestions.currentIndex = 0;
            suggestions.forceActiveFocus();
        }
        Button {
            objectName: "searchButton"
            anchors.right: parent.right
            anchors.rightMargin: 6
            anchors.verticalCenter: parent.verticalCenter
            width: 44
            height: 44
            enabled: box.v.searchable && query.text.trim() !== ""
            Accessible.name: box.t.search
            background: Rectangle {
                radius: 22
                color: parent.down ? box.theme.lavender : box.theme.sage
                border.width: parent.activeFocus ? 2 : 0
                border.color: box.theme.accent
                opacity: parent.enabled ? 1 : 0.5
            }
            contentItem: Image {
                source: "../assets/search-" + (box.theme.dark ? "dark" : "light") + ".svg"
                sourceSize.width: 20
                sourceSize.height: 20
                fillMode: Image.PreserveAspectFit
            }
            onClicked: box.submit()
        }
    }
    ListView {
        id: suggestions
        objectName: "suggestions"
        visible: count > 0
        Layout.fillWidth: true
        Layout.preferredHeight: Math.min(count * 40, 160)
        clip: true
        model: box.v.suggestions
        Accessible.name: box.t.suggestions
        activeFocusOnTab: true
        boundsBehavior: Flickable.StopAtBounds
        Rectangle {
            anchors.fill: parent
            z: -1
            color: box.theme.backdrop
            radius: 12
            border.color: box.theme.line
            border.width: 1
        }
        Keys.onReturnPressed: desktop.acceptSuggestionAndSearch(currentIndex)
        Keys.onEscapePressed: {
            if (box.v.screen === "results")
                desktop.navigate("home");
            else
                query.forceActiveFocus();
        }
        delegate: ItemDelegate {
            required property int index
            required property string modelData
            width: ListView.view.width
            height: 40
            text: modelData
            highlighted: ListView.isCurrentItem
            leftPadding: 16
            rightPadding: 16
            palette.text: box.theme.ink
            palette.buttonText: box.theme.ink
            palette.highlightedText: box.theme.ink
            background: Rectangle {
                color: parent.highlighted || parent.hovered ? box.theme.sage : box.theme.backdrop
                radius: 8
            }
            onClicked: desktop.acceptSuggestionAndSearch(index)
        }
    }
    Connections {
        target: desktop
        function onQueryReplacement(text, cursor) {
            query.text = text;
            query.cursorPosition = cursor;
            query.forceActiveFocus();
        }
    }
}
