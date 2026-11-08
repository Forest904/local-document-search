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
        desktop.search();
    }
    function focusQuery() {
        query.forceActiveFocus();
        query.selectAll();
    }
    spacing: 8
    RowLayout {
        Layout.fillWidth: true
        spacing: 12
        TextField {
            id: query
            objectName: "query"
            Layout.fillWidth: true
            implicitHeight: 56
            leftPadding: 24
            rightPadding: 24
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
        }
        ActionButton {
            objectName: "searchButton"
            iconName: "search"
            theme: box.theme
            text: box.t.search
            primary: true
            enabled: box.v.searchable && query.text.trim() !== ""
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
        Keys.onReturnPressed: desktop.acceptSuggestion(currentIndex)
        Keys.onEscapePressed: query.forceActiveFocus()
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
            onClicked: desktop.acceptSuggestion(index)
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
