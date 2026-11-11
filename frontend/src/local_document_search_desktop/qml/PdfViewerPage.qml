import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Pdf

Item {
    id: page
    objectName: "pdfViewerPage"
    required property var theme
    property var v: desktop.view
    property bool searchOpen: false
    property bool searchSubmitted: false
    property bool findInitialized: false
    property bool jumped: false
    property bool applyingZoom: false
    property string zoomMode: "automatic"
    readonly property var zoomModes: ["automatic", "actual", "page", "width",
                                     "percent:50", "percent:75", "percent:100", "percent:125",
                                     "percent:150", "percent:200", "percent:300", "percent:400"]
    property string warning: ""
    property int topInset: 94
    property int bottomInset: searchOpen ? 52 : 0

    function applyZoom(mode) {
        if (pdfDocument.status !== PdfDocument.Ready) return
        applyingZoom = true
        if (mode === "automatic") pdfView.scaleAutomatic()
        else if (mode === "width") pdfView.renderScale = pdfView.widthScale()
        else if (mode === "page") pdfView.renderScale = pdfView.pageScale()
        else if (mode.startsWith("percent:")) pdfView.renderScale = Number(mode.slice(8)) / 100
        else pdfView.renderScale = 1
        zoomMode = mode
        applyingZoom = false
    }
    function refreshZoom() {
        if (jumped && zoomMode !== "custom")
            Qt.callLater(function () { if (page.jumped && page.zoomMode !== "custom") page.applyZoom(page.zoomMode) })
    }
    function goToNumber() {
        const number = Number(pageNumber.text)
        if (!/^\d+$/.test(pageNumber.text) || number < 1 || number > pdfDocument.pageCount) {
            pageNumber.invalid = true
            return
        }
        pageNumber.invalid = false
        pdfView.goToPage(number - 1)
        pdfView.forceActiveFocus()
    }
    function openFind() {
        if (page.v.viewerTextStatus !== "available") return
        if (!findInitialized) {
            findField.text = page.v.viewerQuery
            findInitialized = true
        }
        searchOpen = true
        findField.forceActiveFocus()
        findField.selectAll()
    }
    function closeFind() {
        searchOpen = false
        searchSubmitted = false
        pdfView.searchString = ""
        pdfView.forceActiveFocus()
    }
    function find(direction) {
        if (!findField.text.trim()) return
        if (!searchSubmitted || pdfView.searchString !== findField.text) {
            pdfView.searchText(findField.text)
            searchSubmitted = true
        } else if (direction < 0) pdfView.searchBack()
        else pdfView.searchForward()
    }
    Shortcut { sequence: "Ctrl+F"; enabled: page.v.viewerTextStatus === "available"; onActivated: page.openFind() }

    PdfDocument { id: pdfDocument; source: page.v.viewerSource }
    LocalPdfMultiPageView {
        id: pdfView
        objectName: "pdfViewer"
        anchors.fill: parent
        z: 0
        topOverlayInset: page.topInset
        bottomOverlayInset: page.bottomInset
        document: pdfDocument
        onRenderScaleChanged: if (page.jumped && !page.applyingZoom) page.zoomMode = "custom"
    }
    Rectangle {
        objectName: "pdfToolbar"
        anchors { left: parent.left; right: parent.right; top: parent.top }
        height: page.topInset
        z: 3
        color: page.theme.surface
        border.color: page.theme.line
        ColumnLayout {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 12
            spacing: 4
            RowLayout {
            Layout.fillWidth: true
            spacing: 6
            ViewerIconButton { theme: page.theme; label: desktop.labels.back; iconName: "back"; onClicked: desktop.navigate("back") }
            Label { text: page.v.viewerName; color: page.theme.ink; elide: Text.ElideMiddle; Layout.fillWidth: true }
            ViewerIconButton { objectName: "pdfPreviousPage"; theme: page.theme; label: desktop.labels.previous; iconName: "next"; rotated: true; enabled: pdfView.currentPage > 0; onClicked: pdfView.goToPage(pdfView.currentPage - 1) }
            ViewerIconButton { objectName: "pdfNextPage"; theme: page.theme; label: desktop.labels.next; iconName: "next"; enabled: pdfView.currentPage >= 0 && pdfView.currentPage < pdfDocument.pageCount - 1; onClicked: pdfView.goToPage(pdfView.currentPage + 1) }
            TextField {
                id: pageNumber
                objectName: "pdfPageNumber"
                property bool invalid: false
                Layout.preferredWidth: 52
                horizontalAlignment: TextInput.AlignHCenter
                text: String(Math.max(0, pdfView.currentPage + 1))
                Accessible.name: desktop.labels.pdfPageNumber
                color: invalid ? page.theme.error : page.theme.ink
                selectionColor: page.theme.sage
                selectedTextColor: page.theme.ink
                placeholderTextColor: page.theme.muted
                background: Rectangle {
                    radius: 8
                    color: page.theme.surface
                    border.color: pageNumber.activeFocus ? page.theme.accent : pageNumber.invalid ? page.theme.error : page.theme.line
                    border.width: pageNumber.activeFocus ? 2 : 1
                }
                onTextEdited: invalid = false
                onAccepted: page.goToNumber()
            }
            Label { text: "/ " + pdfDocument.pageCount; color: page.theme.ink }
            }
            RowLayout {
            Layout.fillWidth: true
            spacing: 6
            ViewerIconButton { objectName: "pdfZoomOut"; theme: page.theme; label: desktop.labels.zoomOut; iconName: "zoom-out"; onClicked: pdfView.zoomBy(1 / 1.15) }
            Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 22; color: page.theme.line }
            ViewerIconButton { objectName: "pdfZoomIn"; theme: page.theme; label: desktop.labels.zoomIn; iconName: "zoom-in"; onClicked: pdfView.zoomBy(1.15) }
            ViewerZoomSelect {
                id: zoomChoice
                objectName: "pdfZoomChoice"
                theme: page.theme
                Layout.preferredWidth: 156
                model: [desktop.labels.pdfAutomaticZoom, desktop.labels.pdfActualSize,
                        desktop.labels.pdfFitPage, desktop.labels.fitWidth,
                        "50%", "75%", "100%", "125%", "150%", "200%", "300%", "400%"]
                currentIndex: 0
                displayText: page.zoomMode === "custom" ? Math.round(pdfView.renderScale * 100) + "%" : model[currentIndex]
                Accessible.name: desktop.labels.pdfZoomMode
                onActivated: page.applyZoom(page.zoomModes[currentIndex])
            }
            Item { Layout.fillWidth: true }
            ViewerIconButton { objectName: "pdfFindButton"; theme: page.theme; label: desktop.labels.pdfFind; iconName: "search"; enabled: page.v.viewerTextStatus === "available"; onClicked: page.openFind() }
            ViewerIconButton { objectName: "pdfRotate"; theme: page.theme; label: desktop.labels.pdfRotate; iconName: "rotate"; onClicked: { pdfView.pageRotation = (pdfView.pageRotation + 90) % 360; page.applyZoom(page.zoomMode === "custom" ? "automatic" : page.zoomMode) } }
            ViewerIconButton { objectName: "openPdfExternally"; theme: page.theme; label: desktop.labels.openExternal; iconName: "external"; onClicked: desktop.openViewerExternally() }
            ViewerIconButton { objectName: "openPdfFolder"; theme: page.theme; label: desktop.labels.openFolder; iconName: "folder"; onClicked: desktop.openViewerFolder() }
            }
        }
    }
    Label {
        objectName: "pdfSearchAvailability"
        anchors { left: parent.left; right: parent.right; top: pdfToolbar.bottom }
        z: 2
        visible: page.v.viewerTextStatus === "checking" || page.v.viewerTextStatus === "unavailable"
        text: page.v.viewerTextStatus === "checking" ? desktop.labels.pdfCheckingText : desktop.labels.pdfNoText
        color: page.theme.muted
        padding: 4
        background: Rectangle { color: page.theme.surface; border.color: page.theme.line }
        Accessible.name: text
    }
    Label {
        objectName: "pdfWarning"
        anchors { left: parent.left; right: parent.right; top: pdfSearchAvailability.visible ? pdfSearchAvailability.bottom : pdfToolbar.bottom }
        z: 2
        visible: pdfDocument.status === PdfDocument.Error || page.warning !== ""
        text: pdfDocument.status === PdfDocument.Error ? desktop.labels.pdfOpenError : page.warning
        color: page.theme.error
        padding: 4
        background: Rectangle { color: page.theme.surface; border.color: page.theme.line }
        wrapMode: Text.Wrap
    }
    Rectangle {
        objectName: "pdfFindBar"
        parent: Overlay.overlay
        visible: page.searchOpen
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        height: page.bottomInset
        z: 100
        color: page.theme.surface
        border.color: page.theme.line
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: 16
            spacing: 8
            TextField {
                id: findField
                objectName: "pdfFindField"
                Layout.preferredWidth: 300
                Layout.maximumWidth: 340
                placeholderText: desktop.labels.pdfFind
                Accessible.name: desktop.labels.pdfFind
                color: page.theme.ink
                selectionColor: page.theme.sage
                selectedTextColor: page.theme.ink
                placeholderTextColor: page.theme.muted
                background: Rectangle {
                    radius: 8
                    color: page.theme.surface
                    border.color: findField.activeFocus ? page.theme.accent : page.theme.line
                    border.width: findField.activeFocus ? 2 : 1
                }
                onTextEdited: { page.searchSubmitted = false; pdfView.searchString = "" }
                onAccepted: page.find((Qt.application.keyboardModifiers & Qt.ShiftModifier) ? -1 : 1)
            }
            ViewerIconButton { theme: page.theme; label: desktop.labels.previous; iconName: "next"; rotated: true; enabled: findField.text.trim() !== ""; onClicked: page.find(-1) }
            ViewerIconButton { theme: page.theme; label: desktop.labels.next; iconName: "next"; enabled: findField.text.trim() !== ""; onClicked: page.find(1) }
            CheckBox {
                id: highlightCheck
                objectName: "pdfHighlightAll"
                text: desktop.labels.pdfHighlightAll
                Accessible.name: text
                checked: false
                indicator: Rectangle {
                    implicitWidth: 18
                    implicitHeight: 18
                    x: highlightCheck.leftPadding
                    y: (highlightCheck.height - height) / 2
                    radius: 5
                    color: highlightCheck.checked ? page.theme.sage : page.theme.surface
                    border.color: highlightCheck.activeFocus ? page.theme.accent : page.theme.line
                    border.width: highlightCheck.activeFocus ? 2 : 1
                    Text { anchors.centerIn: parent; text: highlightCheck.checked ? "✓" : ""; color: page.theme.ink }
                }
                contentItem: Text {
                    text: highlightCheck.text
                    color: highlightCheck.enabled ? page.theme.ink : page.theme.muted
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: highlightCheck.indicator.width + highlightCheck.spacing
                }
                onToggled: pdfView.highlightAll = checked
            }
            Label {
                color: page.theme.muted
                text: !page.searchSubmitted ? "" : pdfView.searchRunning ? desktop.labels.pdfSearching : pdfView.searchCount === 0 ? desktop.labels.pdfNoMatches
                      : (pdfView.searchIndex + 1) + " / " + pdfView.searchCount
            }
            Item { Layout.fillWidth: true }
            ViewerIconButton { theme: page.theme; label: desktop.labels.close; iconName: "close"; onClicked: page.closeFind() }
        }
    }
    function jumpOnce() {
        if (jumped || pdfDocument.status !== PdfDocument.Ready || pdfView.width <= 0 || pdfView.height <= 0) return
        jumped = true
        let target = page.v.viewerPage
        if (target >= pdfDocument.pageCount || target < 0) {
            target = 0
            warning = desktop.labels.pdfPageUnavailable
        }
        Qt.callLater(function () {
            page.applyingZoom = true
            pdfView.scaleAutomatic(target)
            page.zoomMode = "automatic"
            page.applyingZoom = false
            pdfView.goToPage(target)
        })
    }
    Connections { target: pdfDocument; function onStatusChanged() { page.jumpOnce() } }
    Connections {
        target: pdfView
        function onWidthChanged() { page.jumpOnce(); page.refreshZoom() }
        function onHeightChanged() { page.jumpOnce(); page.refreshZoom() }
        function onCurrentPageChanged() {
            if (!pageNumber.activeFocus) pageNumber.text = String(Math.max(0, pdfView.currentPage + 1))
            page.refreshZoom()
        }
    }
    Component.onCompleted: jumpOnce()
}
