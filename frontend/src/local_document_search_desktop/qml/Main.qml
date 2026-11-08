import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Dialogs

ApplicationWindow {
    id: root
    objectName: "mainWindow"
    visible: true
    width: Math.min(1280, Screen.desktopAvailableWidth - 32)
    height: Math.min(820, Screen.desktopAvailableHeight - 60)
    minimumWidth: 900
    minimumHeight: 640
    title: "Local Document Search"
    property var v: desktop.view
    property var t: desktop.labels
    property bool dark: v.theme === "dark"
    property color surface: dark ? "#242629" : "#ffffff"
    property color backdrop: dark ? "#1a1c1e" : "#f6f7f9"
    property color ink: dark ? "#f1f3f5" : "#20252b"
    property color muted: dark ? "#b8c0cb" : "#535e6c"
    property color line: dark ? "#4c535e" : "#c7cdd5"
    property color accent: dark ? "#9fc5ff" : "#225aa8"
    color: surface
    font.family: "Segoe UI"
    font.pixelSize: 14
    palette.window: surface
    palette.windowText: ink
    palette.text: ink
    palette.placeholderText: muted
    palette.base: surface
    palette.button: backdrop
    palette.buttonText: ink
    palette.highlight: accent
    palette.highlightedText: dark ? "#152033" : "#ffffff"
    palette.mid: line
    palette.dark: line
    palette.light: surface
    onClosing: function(close) {
        close.accepted = v.closed
        if (!close.accepted) desktop.requestClose()
    }
    Connections {
        target: desktop
        function onCloseReady() { root.close() }
        function onQueryReplacement(text, cursor) {
            query.text = text
            query.cursorPosition = cursor
            query.forceActiveFocus()
        }
    }
    Shortcut { sequence: "Ctrl+L"; onActivated: { query.forceActiveFocus(); query.selectAll() } }
    Shortcut { sequence: "Ctrl+O"; enabled: v.canManage; onActivated: folderDialog.open() }
    Shortcut { sequence: "F5"; enabled: v.canManage && v.directory !== ""; onActivated: desktop.action("sync") }

    component Caption: Label {
        color: root.muted
        textFormat: Text.PlainText
        wrapMode: Text.Wrap
    }
    component Action: Button {
        id: control
        activeFocusOnTab: true
        Accessible.name: text
        background: Rectangle {
            radius: 7
            color: control.down ? root.line : control.hovered ? (root.dark ? "#373d46" : "#e8edf4") : root.backdrop
            border.color: control.activeFocus ? root.accent : root.line
            border.width: control.activeFocus ? 2 : 1
            opacity: control.enabled ? 1 : 0.5
        }
        contentItem: Text {
            text: control.text
            font: control.font
            color: control.enabled ? root.ink : root.muted
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        implicitHeight: 38
        leftPadding: 12
        rightPadding: 12
    }
    FolderDialog {
        id: folderDialog
        title: t.choose
        onAccepted: desktop.chooseDirectory(selectedFolder.toString())
    }
    Dialog {
        id: clearDialog
        title: t.clearTitle
        anchors.centerIn: parent
        width: Math.min(480, root.width - 64)
        modal: true
        contentItem: ColumnLayout {
            Label { text: t.clearBody; textFormat: Text.PlainText; wrapMode: Text.Wrap; Layout.fillWidth: true }
            RowLayout {
                Layout.alignment: Qt.AlignRight
                Action { text: t.back; onClicked: clearDialog.close() }
                Action { text: t.delete; enabled: v.canManage; onClicked: { clearDialog.close(); desktop.action("clear") } }
            }
        }
    }
    Dialog {
        id: diagnosticsDialog
        title: t.details
        anchors.centerIn: parent
        width: Math.min(660, root.width - 64)
        height: Math.min(480, root.height - 64)
        modal: true
        standardButtons: Dialog.Close
        contentItem: ScrollView {
            TextArea { text: v.diagnostics; readOnly: true; textFormat: TextEdit.PlainText; wrapMode: TextEdit.Wrap; Accessible.name: t.details }
        }
    }
    RowLayout {
        anchors.fill: parent
        spacing: 0
        Rectangle {
            Layout.preferredWidth: 246
            Layout.fillHeight: true
            color: backdrop
            ScrollView {
                id: sidebarScroll
                anchors.fill: parent
                anchors.margins: 18
                contentWidth: availableWidth
                clip: true
                ColumnLayout {
                    width: sidebarScroll.availableWidth
                    spacing: 12
                    Label { text: "LOCAL DOCUMENT SEARCH"; font.pixelSize: 12; font.bold: true; color: muted }
                    Label { text: t.app; font.pixelSize: 23; font.bold: true; color: ink; Layout.fillWidth: true; wrapMode: Text.Wrap }
                    Caption { text: t.tagline; Layout.fillWidth: true }
                    Rectangle { Layout.fillWidth: true; height: 1; color: line; Layout.topMargin: 8; Layout.bottomMargin: 8 }
                    Caption { text: v.directory || t.none; Layout.fillWidth: true; Accessible.name: text }
                    Action { objectName: "chooseButton"; text: t.choose; Layout.fillWidth: true; enabled: v.canManage; onClicked: folderDialog.open() }
                    Action { objectName: "syncButton"; text: t.sync; Layout.fillWidth: true; enabled: v.canManage && v.directory !== ""; onClicked: desktop.action("sync") }
                    Label { text: t.filters; font.bold: true; Layout.topMargin: 12 }
                    Caption { text: t.formats }
                    RowLayout {
                        spacing: 0
                        CheckBox { id: txt; text: "TXT"; checked: true; padding: 2; spacing: 2; font.pixelSize: 12; onClicked: root.optionsChanged() }
                        CheckBox { id: md; text: "MD"; checked: true; padding: 2; spacing: 2; font.pixelSize: 12; onClicked: root.optionsChanged() }
                        CheckBox { id: pdf; text: "PDF"; checked: true; padding: 2; spacing: 2; font.pixelSize: 12; onClicked: root.optionsChanged() }
                    }
                    TextField {
                        id: relativeFolder
                        objectName: "folderFilter"
                        Layout.fillWidth: true
                        placeholderText: t.folder
                        Accessible.name: t.folder
                        onTextEdited: root.optionsChanged()
                    }
                    Caption { text: t.order }
                    ComboBox {
                        id: order
                        objectName: "order"
                        Layout.fillWidth: true
                        model: [t.relevance, t.path]
                        Accessible.name: t.order
                        onActivated: root.optionsChanged()
                    }
                    Label { text: t.settings; font.bold: true; Layout.topMargin: 12 }
                    Caption { text: t.language }
                    ComboBox {
                        objectName: "language"
                        Layout.fillWidth: true
                        model: ["Italiano", "English"]
                        currentIndex: v.language === "it" ? 0 : 1
                        enabled: v.ready
                        Accessible.name: t.language
                        onActivated: desktop.savePreferences(currentIndex === 0 ? "it" : "en", v.theme)
                    }
                    Caption { text: t.theme }
                    ComboBox {
                        objectName: "theme"
                        Layout.fillWidth: true
                        model: [t.light, t.dark]
                        currentIndex: v.theme === "light" ? 0 : 1
                        enabled: v.ready
                        Accessible.name: t.theme
                        onActivated: desktop.savePreferences(v.language, currentIndex === 0 ? "light" : "dark")
                    }
                    Action { text: t.rebuild; Layout.fillWidth: true; enabled: v.canManage && v.directory !== ""; onClicked: desktop.action("rebuild") }
                    Action { text: t.recover; Layout.fillWidth: true; enabled: v.canManage && v.directory !== ""; onClicked: desktop.action("recover") }
                    Action { text: t.clear; Layout.fillWidth: true; enabled: v.canManage; onClicked: clearDialog.open() }
                }
            }
        }
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 24
            spacing: 14
            ColumnLayout {
                visible: !v.initialized
                Layout.fillWidth: true
                Layout.fillHeight: true
                Item { Layout.fillHeight: true }
                Label { text: t.privacyTitle; font.pixelSize: 30; font.bold: true; Layout.fillWidth: true; wrapMode: Text.Wrap }
                Caption { text: t.privacy; Layout.fillWidth: true; font.pixelSize: 16 }
                Action { objectName: "continueButton"; text: v.busy ? t.loading : t.continue; enabled: !v.busy && !v.closing; onClicked: desktop.initialize(); Layout.topMargin: 12; Component.onCompleted: forceActiveFocus() }
                Item { Layout.fillHeight: true }
            }
            ColumnLayout {
                visible: v.initialized
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 12
                RowLayout {
                    Layout.fillWidth: true
                    TextField {
                        id: query
                        objectName: "query"
                        Layout.fillWidth: true
                        implicitHeight: 46
                        placeholderText: t.query
                        Accessible.name: t.search
                        enabled: v.searchable
                        selectByMouse: true
                        onTextEdited: desktop.editQuery(text, cursorPosition)
                        onCursorPositionChanged: desktop.editQuery(text, cursorPosition)
                        onAccepted: desktop.search()
                        Keys.onDownPressed: if (suggestions.count > 0) { suggestions.currentIndex = 0; suggestions.forceActiveFocus() }
                    }
                    ComboBox {
                        id: field
                        objectName: "field"
                        Layout.preferredWidth: 190
                        model: [t.both, t.filename, t.content]
                        Accessible.name: t.field
                        onActivated: root.optionsChanged()
                    }
                    Action { text: t.search; enabled: v.searchable; onClicked: desktop.search() }
                }
                Caption { text: t.hint; Layout.fillWidth: true; font.pixelSize: 12 }
                ListView {
                    id: suggestions
                    objectName: "suggestions"
                    visible: count > 0
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.min(count * 34, 170)
                    clip: true
                    model: v.suggestions
                    Accessible.name: t.suggestions
                    activeFocusOnTab: true
                    Keys.onReturnPressed: desktop.acceptSuggestion(currentIndex)
                    Keys.onEscapePressed: query.forceActiveFocus()
                    delegate: ItemDelegate {
                        required property int index
                        required property string modelData
                        width: ListView.view.width
                        height: 34
                        text: modelData
                        highlighted: ListView.isCurrentItem
                        onClicked: desktop.acceptSuggestion(index)
                    }
                }
                RowLayout {
                    Label { text: t.results; font.pixelSize: 20; font.bold: true }
                    Caption { text: v.hasResponse ? String(v.total) : "" }
                    Item { Layout.fillWidth: true }
                    BusyIndicator { running: v.reading; visible: running; implicitWidth: 24; implicitHeight: 24; Accessible.name: t.loading }
                }
                SplitView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    orientation: Qt.Horizontal
                    Rectangle {
                        SplitView.preferredWidth: 480
                        SplitView.minimumWidth: 220
                        color: surface
                        ListView {
                            id: results
                            objectName: "results"
                            anchors.fill: parent
                            clip: true
                            spacing: 8
                            model: desktop.results
                            currentIndex: -1
                            activeFocusOnTab: true
                            Accessible.name: t.results
                            ScrollBar.vertical: ScrollBar {}
                            Keys.onReturnPressed: if (currentIndex >= 0) desktop.selectResult(currentIndex)
                            onCurrentIndexChanged: if (activeFocus && currentIndex >= 0) desktop.selectResult(currentIndex)
                            delegate: ItemDelegate {
                                id: result
                                required property int index
                                required property string nameHtml
                                required property string pathText
                                required property string snippetHtml
                                required property string accessibleText
                                width: ListView.view.width - 12
                                height: resultText.implicitHeight + 24
                                Accessible.name: accessibleText
                                Accessible.role: Accessible.ListItem
                                highlighted: ListView.isCurrentItem
                                background: Rectangle {
                                    radius: 8
                                    color: result.highlighted ? (root.dark ? "#303f53" : "#eaf1fb") : backdrop
                                    border.color: result.activeFocus || (results.activeFocus && result.highlighted) ? accent : line
                                    border.width: result.activeFocus || (results.activeFocus && result.highlighted) ? 2 : 1
                                }
                                contentItem: Column {
                                    id: resultText
                                    spacing: 6
                                    Text { width: parent.width; text: result.nameHtml; textFormat: Text.RichText; color: ink; font.pixelSize: 16; wrapMode: Text.Wrap }
                                    Text { width: parent.width; text: result.pathText; textFormat: Text.PlainText; color: muted; font.pixelSize: 12; elide: Text.ElideMiddle }
                                    Text { width: parent.width; text: result.snippetHtml; textFormat: Text.RichText; color: ink; wrapMode: Text.Wrap; maximumLineCount: 4; elide: Text.ElideRight }
                                }
                                onClicked: { results.currentIndex = index; desktop.selectResult(index) }
                            }
                        }
                        Caption {
                            anchors.centerIn: parent
                            width: parent.width - 32
                            horizontalAlignment: Text.AlignHCenter
                            visible: results.count === 0
                            text: v.hasResponse ? t.empty : v.searchable ? t.enter : t.building
                        }
                    }
                    Rectangle {
                        SplitView.fillWidth: true
                        SplitView.minimumWidth: 220
                        color: backdrop
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 16
                            Label { text: t.preview; font.bold: true; font.pixelSize: 18 }
                            Caption { text: v.selectedPath || t.select; Layout.fillWidth: true }
                            ScrollView {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                TextArea {
                                    objectName: "preview"
                                    text: v.preview
                                    textFormat: TextEdit.RichText
                                    readOnly: true
                                    selectByMouse: true
                                    activeFocusOnTab: true
                                    wrapMode: TextEdit.Wrap
                                    color: ink
                                    Accessible.name: t.preview
                                    background: Rectangle { color: "transparent"; border.color: parent.activeFocus ? accent : "transparent" }
                                }
                            }
                            Action { text: t.open; enabled: v.selectedPath !== "" && v.searchable; onClicked: desktop.openSelected() }
                        }
                    }
                }
                RowLayout {
                    Action { text: t.previous; enabled: v.canPrevious; onClicked: desktop.page(-1) }
                    Caption { text: v.hasResponse ? (v.total ? String(v.offset + 1) + "–" + Math.min(v.offset + 50, v.total) + " / " + v.total : "0") : "" }
                    Item { Layout.fillWidth: true }
                    Action { text: t.next; enabled: v.canNext; onClicked: desktop.page(1) }
                }
            }
            Rectangle { Layout.fillWidth: true; height: 1; color: line }
            Caption { text: v.status; Layout.fillWidth: true; Accessible.name: text }
            RowLayout {
                visible: v.running
                Layout.fillWidth: true
                Caption { text: v.phase + " · " + v.counts }
                ProgressBar { Layout.fillWidth: true; indeterminate: v.progress < 0; value: Math.max(0, v.progress); Accessible.name: v.phase }
                Action { text: t.cancel; enabled: v.canCancel; onClicked: desktop.action("cancel") }
            }
            RowLayout {
                visible: v.message !== ""
                Layout.fillWidth: true
                Label { text: v.message; textFormat: Text.PlainText; wrapMode: Text.Wrap; color: root.dark ? "#ffbcab" : "#9b3019"; Layout.fillWidth: true; Accessible.name: text }
                Action { text: t.retry; enabled: v.canManage && v.directory !== ""; onClicked: desktop.action("retry") }
            }
            Action { text: t.details; visible: v.diagnostics !== ""; onClicked: diagnosticsDialog.open() }
        }
    }
    function optionsChanged() {
        let formats = []
        if (txt.checked) formats.push("txt")
        if (md.checked) formats.push("md")
        if (pdf.checked) formats.push("pdf")
        desktop.setOptions(["both", "filename", "content"][field.currentIndex], formats,
                           relativeFolder.text, order.currentIndex === 0 ? "relevance" : "path")
    }
}
