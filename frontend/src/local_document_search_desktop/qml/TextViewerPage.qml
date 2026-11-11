import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Item {
    id: page
    signal chooseRequested()
    objectName: "textViewerPage"
    required property var theme
    property var reader: desktop.textReader
    property bool searchOpen: false
    property bool submitted: false
    property bool wrap: true
    property var gutterRows: []
    property bool confirmExit: false
    property string pendingExit: ""
    function requestLeave(action) {
        if (reader.saving) return
        if (reader.dirty) { pendingExit = action; confirmExit = true; return }
        finishLeave(action)
    }
    function finishLeave(action) {
        pendingExit = ""
        if (action === "close") desktop.requestClose()
        else {
            if (action === "choose") chooseRequested()
            desktop.navigate("back")
        }
    }

    function refreshGutter() {
        if (!reader.ready) { gutterRows = []; return }
        reader.refreshLayout()
        gutterRows = reader.visibleLines(scroll.contentItem.contentY, scroll.height)
    }
    function openFind() {
        if (!reader.ready) return
        searchOpen = true
        findField.forceActiveFocus()
        findField.selectAll()
    }
    function closeFind() {
        searchOpen = false
        submitted = false
        reader.clearFind()
        area.forceActiveFocus()
    }
    function find(direction) {
        if (!reader.ready || !findField.text || /[\r\n]/.test(findField.text)) return
        reader.find(findField.text, direction)
        submitted = true
    }
    function jump(start, end) {
        if (!reader.ready) return
        if (reader.mode === "preview") {
            const target = reader.marker === "manual" ? [start, end] : reader.previewTarget
            if (target.length !== 2) return
            previewArea.select(target[0], target[1])
            const previewRect = previewArea.positionToRectangle(target[0])
            previewScroll.contentItem.contentY = Math.max(0, previewRect.y - previewScroll.height * 0.3)
            return
        }
        area.select(start, end)
        const rectangle = area.positionToRectangle(start)
        scroll.contentItem.contentY = Math.max(0, rectangle.y - scroll.height * 0.3)
        if (!searchOpen) area.forceActiveFocus()
        refreshGutter()
    }

    Shortcut { sequence: "Ctrl+F"; enabled: reader.ready; onActivated: page.openFind() }
    Shortcut { sequence: "Ctrl+S"; enabled: reader.ready && reader.dirty && !reader.saving; onActivated: reader.save() }
    Connections {
        target: reader
        function onChanged() {
            Qt.callLater(page.refreshGutter)
            if (page.pendingExit !== "" && !reader.saving && reader.errorKey !== "")
                page.pendingExit = ""
        }
        function onGutterChanged() { Qt.callLater(page.refreshGutter) }
        function onJumpRequested(start, end) { Qt.callLater(function() { page.jump(start, end) }) }
        function onSaveCompleted() { if (page.pendingExit !== "") page.finishLeave(page.pendingExit) }
    }
    Connections {
        target: scroll.contentItem
        function onContentYChanged() { Qt.callLater(page.refreshGutter) }
    }
    Connections {
        target: page.theme
        function onDarkChanged() { reader.setDark(page.theme.dark) }
    }
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        Rectangle {
            objectName: "textToolbar"
            Layout.fillWidth: true
            Layout.preferredHeight: 50
            color: page.theme.surface
            border.color: page.theme.line
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                spacing: 8
                ViewerIconButton { theme: page.theme; label: desktop.labels.back; iconName: "back"; onClicked: page.requestLeave("back") }
                Label { text: reader.filename; color: page.theme.ink; elide: Text.ElideMiddle; Layout.fillWidth: true; Accessible.name: text }
                Label { text: reader.dirty ? "●" : reader.editing ? desktop.labels.textEdit : desktop.labels.textReadOnly; color: page.theme.muted; Accessible.name: text }
                Button { text: reader.editing ? desktop.labels.textReading : desktop.labels.textEdit; enabled: reader.ready && !reader.saving; onClicked: reader.editing ? reader.stopEditing() : reader.startEditing() }
                Button { text: desktop.labels.textSave; enabled: reader.ready && reader.dirty && !reader.saving; onClicked: reader.save() }
                Button { text: desktop.labels.textCopyDraft; visible: reader.errorKey === "TextViewConflict"; onClicked: reader.copyDraft() }
                Button { text: desktop.labels.textReload; visible: reader.errorKey === "TextViewConflict"; onClicked: reloadDialog.open() }
                ViewerIconButton { objectName: "textFindButton"; theme: page.theme; label: desktop.labels.textFind; iconName: "search"; enabled: reader.ready; onClicked: page.openFind() }
                Button {
                    objectName: "textWrapButton"
                    text: desktop.labels.textWrap
                    checkable: true
                    checked: page.wrap
                    Accessible.name: text
                    activeFocusOnTab: true
                    implicitHeight: 32
                    background: Rectangle {
                        radius: 8
                        color: page.wrap ? page.theme.sage : page.theme.surface
                        border.color: parent.activeFocus ? page.theme.accent : page.theme.line
                        border.width: parent.activeFocus ? 2 : 1
                    }
                    contentItem: Text {
                        text: parent.text
                        color: page.theme.ink
                        font.pixelSize: 13
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: { page.wrap = checked; Qt.callLater(page.refreshGutter) }
                }
                ViewerIconButton { theme: page.theme; label: desktop.labels.openExternal; iconName: "external"; onClicked: desktop.openViewerExternally() }
                ViewerIconButton { theme: page.theme; label: desktop.labels.openFolder; iconName: "folder"; onClicked: desktop.openViewerFolder() }
            }
        }
        Label {
            Layout.fillWidth: true
            visible: reader.saving || reader.syncWarning || (reader.errorKey !== "" && reader.state === "ready")
            text: reader.saving ? desktop.labels.textSaving : reader.syncWarning ? desktop.labels.textSyncWarning : desktop.labels[reader.errorKey] || reader.errorKey
            color: reader.errorKey !== "" ? page.theme.error : page.theme.muted
            padding: 8
            Accessible.name: text
        }
        Flickable {
            Layout.fillWidth: true
            Layout.preferredHeight: reader.editing && reader.markdown ? 42 : 0
            visible: reader.editing && reader.markdown
            contentWidth: formatRow.implicitWidth
            clip: true
            RowLayout {
                id: formatRow
                spacing: 4
                Repeater {
                    model: ["H1", "H2", "H3", "H4", "H5", "H6", "B", "I", "•", "1.", "❝", "🔗", "</>", "```"]
                    Button {
                        required property int index
                        required property string modelData
                        text: modelData
                        Accessible.name: modelData
                        onClicked: {
                            const kinds = ["h1", "h2", "h3", "h4", "h5", "h6", "bold", "italic", "bullet", "number", "quote", "link", "code", "block"]
                            reader.formatSelection(kinds[index], area.selectionStart, area.selectionEnd)
                            area.forceActiveFocus()
                        }
                    }
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            visible: reader.state === "loading" || reader.state === "populating" || reader.state === "error"
            Label {
                objectName: "textReadStatus"
                text: reader.state === "error" ? desktop.labels[reader.errorKey] || desktop.labels.failure
                      : desktop.labels.loading
                color: reader.state === "error" ? page.theme.error : page.theme.muted
                padding: 8
                Layout.fillWidth: true
                Accessible.name: text
            }
            Button {
                text: reader.state === "error" ? desktop.labels.retry : desktop.labels.textCancelLoad
                Accessible.name: text
                onClicked: reader.state === "error" ? desktop.retryTextViewer() : desktop.navigate("back")
            }
        }
        Label {
            objectName: "textWarning"
            Layout.fillWidth: true
            visible: reader.warningKey !== ""
            text: reader.warningKey === "changed" ? desktop.labels.textChanged : desktop.labels.textPositionUnavailable
            color: page.theme.error
            padding: 8
            wrapMode: Text.Wrap
            Accessible.name: text
        }
        Label {
            Layout.fillWidth: true
            visible: reader.marker === "snapshot" || reader.marker === "manual"
            text: reader.marker === "snapshot" ? desktop.labels.textSnapshotMatch : desktop.labels.textManualMatch
            color: page.theme.muted
            padding: 4
            Accessible.name: text
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: reader.mode !== "preview"
            spacing: 0
            Rectangle {
                Layout.preferredWidth: 60
                Layout.fillHeight: true
                color: page.theme.backdrop
                border.color: page.theme.line
                clip: true
                Repeater {
                    model: page.gutterRows
                    delegate: Label {
                        x: 4
                        y: modelData.y - scroll.contentItem.contentY + 8
                        width: 48
                        height: 20
                        horizontalAlignment: Text.AlignRight
                        text: String(modelData.number)
                        font.family: "Consolas"
                        font.pixelSize: 12
                        color: page.theme.muted
                        Accessible.ignored: true
                    }
                }
            }
            ScrollView {
                id: scroll
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                onWidthChanged: { reader.invalidateLayout(); Qt.callLater(page.refreshGutter) }
                onHeightChanged: Qt.callLater(page.refreshGutter)
                TextArea {
                    id: area
                    objectName: "textReaderArea"
                    width: scroll.availableWidth
                    readOnly: !reader.editing || reader.saving
                    textFormat: TextEdit.PlainText
                    selectByMouse: true
                    selectByKeyboard: true
                    wrapMode: page.wrap ? TextEdit.Wrap : TextEdit.NoWrap
                    font.family: "Consolas"
                    font.pixelSize: 15
                    color: page.theme.ink
                    selectionColor: page.theme.accent
                    selectedTextColor: page.theme.backdrop
                    padding: 8
                    Accessible.name: reader.filename + ", " + desktop.labels.textReadOnly
                    background: Rectangle { color: page.theme.surface }
                    Component.onCompleted: reader.attach(textDocument)
                    onWidthChanged: { reader.invalidateLayout(); Qt.callLater(page.refreshGutter) }
                }
            }
        }
        ScrollView {
            id: previewScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: reader.mode === "preview"
            clip: true
            TextArea {
                id: previewArea
                objectName: "markdownPreviewArea"
                width: previewScroll.availableWidth
                text: reader.previewHtml
                textFormat: TextEdit.RichText
                onLinkActivated: function(link) { reader.copyLink(link) }
                readOnly: true
                selectByMouse: true
                padding: 32
                color: page.theme.ink
                background: Rectangle { color: page.theme.surface }
                Accessible.name: reader.filename
            }
        }
        Rectangle {
            objectName: "textFindBar"
            Layout.fillWidth: true
            Layout.preferredHeight: page.searchOpen ? 52 : 0
            visible: page.searchOpen
            color: page.theme.surface
            border.color: page.theme.line
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                spacing: 8
                TextField {
                    id: findField
                    objectName: "textFindField"
                    Layout.preferredWidth: 300
                    Layout.maximumWidth: 340
                    placeholderText: desktop.labels.textFind
                    property bool invalidInput: /[\r\n]/.test(text)
                    Accessible.name: desktop.labels.textFind
                    color: page.theme.ink
                    selectionColor: page.theme.sage
                    selectedTextColor: page.theme.ink
                    background: Rectangle {
                        radius: 8
                        color: page.theme.surface
                        border.color: findField.activeFocus ? page.theme.accent : page.theme.line
                        border.width: findField.activeFocus ? 2 : 1
                    }
                    onTextEdited: { page.submitted = false; reader.clearFind() }
                    onAccepted: page.find((Qt.application.keyboardModifiers & Qt.ShiftModifier) ? -1 : 1)
                }
                ViewerIconButton { theme: page.theme; label: desktop.labels.previous; iconName: "next"; rotated: true; enabled: findField.text !== ""; onClicked: page.find(-1) }
                ViewerIconButton { theme: page.theme; label: desktop.labels.next; iconName: "next"; enabled: findField.text !== ""; onClicked: page.find(1) }
                Label {
                    color: page.theme.muted
                    text: findField.invalidInput ? desktop.labels.textFindSingleLine : !page.submitted ? "" : reader.searching ? desktop.labels.pdfSearching : reader.matchCount === 0 ? desktop.labels.pdfNoMatches : reader.matchIndex + " / " + reader.matchCount + (reader.wrapped ? " · " + desktop.labels.textWrapped : "")
                    Accessible.name: text
                }
                Item { Layout.fillWidth: true }
                ViewerIconButton { theme: page.theme; label: desktop.labels.close; iconName: "close"; onClicked: page.closeFind() }
            }
        }
    }
    Component.onCompleted: reader.setDark(page.theme.dark)
    Dialog {
        id: unsavedDialog
        objectName: "unsavedTextDialog"
        modal: true
        title: desktop.labels.textUnsaved
        visible: page.confirmExit
        anchors.centerIn: parent
        contentItem: ColumnLayout {
            Label { text: desktop.labels.textSaveBeforeExit }
            RowLayout {
                Button { text: desktop.labels.textSave; onClicked: { page.confirmExit = false; reader.save() } }
                Button { text: desktop.labels.textDiscard; onClicked: { page.confirmExit = false; reader.discard(); page.finishLeave(page.pendingExit) } }
                Button { text: desktop.labels.cancel; onClicked: { page.confirmExit = false; page.pendingExit = "" } }
            }
        }
        onRejected: { page.confirmExit = false; page.pendingExit = "" }
    }
    Dialog {
        id: reloadDialog
        modal: true
        title: desktop.labels.textReload
        anchors.centerIn: parent
        contentItem: ColumnLayout {
            Label { text: desktop.labels.textUnsaved }
            RowLayout {
                Button { text: desktop.labels.textReload; onClicked: { reloadDialog.close(); desktop.retryTextViewer() } }
                Button { text: desktop.labels.cancel; onClicked: reloadDialog.close() }
            }
        }
    }
    Component.onDestruction: reader.detach()
    onWrapChanged: { reader.invalidateLayout(); Qt.callLater(page.refreshGutter) }
}
