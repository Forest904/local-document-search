import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Pdf

ColumnLayout {
    id: page
    required property var theme
    property var v: desktop.view
    property bool searchOpen: false
    property string warning: ""
    property bool jumped: false
    property bool searchSubmitted: false
    property bool findInitialized: false
    spacing: 8

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
        } else if (direction < 0) {
            pdfView.searchBack()
        } else {
            pdfView.searchForward()
        }
    }
    Shortcut {
        sequence: "Ctrl+F"
        enabled: page.v.viewerTextStatus === "available"
        onActivated: page.openFind()
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 5
        ViewerIconButton { theme: page.theme; label: desktop.labels.back; iconName: "back"; onClicked: desktop.navigate("back") }
        Label { text: page.v.viewerName; color: page.theme.ink; elide: Text.ElideMiddle; Layout.fillWidth: true }
        Label { text: desktop.labels.page + " " + Math.max(0, pdfView.currentPage + 1) + " / " + pdfDocument.pageCount; color: page.theme.ink }
        ViewerIconButton { objectName: "pdfFindButton"; theme: page.theme; label: desktop.labels.pdfFind; iconName: "search"; enabled: page.v.viewerTextStatus === "available"; onClicked: page.openFind() }
        ViewerIconButton { objectName: "pdfZoomOut"; theme: page.theme; label: desktop.labels.zoomOut; iconName: "zoom-out"; onClicked: pdfView.zoomBy(1 / 1.15) }
        ViewerIconButton { objectName: "pdfZoomIn"; theme: page.theme; label: desktop.labels.zoomIn; iconName: "zoom-in"; onClicked: pdfView.zoomBy(1.15) }
        ViewerIconButton { objectName: "pdfFitWidth"; theme: page.theme; label: desktop.labels.fitWidth; iconName: "fit"; onClicked: pdfView.scaleToWidth(pdfView.width, pdfView.height) }
        ViewerIconButton { objectName: "openPdfExternally"; theme: page.theme; label: desktop.labels.openExternal; iconName: "external"; onClicked: desktop.openViewerExternally() }
        ViewerIconButton { objectName: "openPdfFolder"; theme: page.theme; label: desktop.labels.openFolder; iconName: "folder"; onClicked: desktop.openViewerFolder() }
    }

    RowLayout {
        visible: page.searchOpen
        Layout.fillWidth: true
        spacing: 5
        TextField {
            id: findField
            objectName: "pdfFindField"
            Layout.fillWidth: true
            placeholderText: desktop.labels.pdfFind
            Accessible.name: desktop.labels.pdfFind
            onTextEdited: {
                page.searchSubmitted = false
                pdfView.searchString = ""
            }
            onAccepted: page.find((Qt.application.keyboardModifiers & Qt.ShiftModifier) ? -1 : 1)
            Keys.onEscapePressed: page.closeFind()
        }
        Label {
            color: page.theme.muted
            text: !page.searchSubmitted ? "" : pdfView.searchCount === 0 ? desktop.labels.pdfNoMatches
                  : (pdfView.searchIndex + 1) + " / " + pdfView.searchCount
        }
        ViewerIconButton { theme: page.theme; label: desktop.labels.previous; iconName: "next"; rotated: true; enabled: findField.text.trim() !== ""; onClicked: page.find(-1) }
        ViewerIconButton { theme: page.theme; label: desktop.labels.next; iconName: "next"; enabled: findField.text.trim() !== ""; onClicked: page.find(1) }
        ViewerIconButton { theme: page.theme; label: desktop.labels.close; iconName: "close"; onClicked: page.closeFind() }
    }

    Label {
        objectName: "pdfSearchAvailability"
        visible: page.v.viewerTextStatus === "checking" || page.v.viewerTextStatus === "unavailable"
        text: page.v.viewerTextStatus === "checking" ? desktop.labels.pdfCheckingText : desktop.labels.pdfNoText
        color: page.theme.muted
        Layout.fillWidth: true
        Accessible.name: text
    }
    Label {
        objectName: "pdfWarning"
        visible: pdfDocument.status === PdfDocument.Error || page.warning !== ""
        text: pdfDocument.status === PdfDocument.Error ? desktop.labels.pdfOpenError : page.warning
        color: page.theme.error
        Layout.fillWidth: true
        wrapMode: Text.Wrap
    }
    PdfDocument { id: pdfDocument; source: page.v.viewerSource }
    LocalPdfMultiPageView {
        id: pdfView
        objectName: "pdfViewer"
        Layout.fillWidth: true
        Layout.fillHeight: true
        document: pdfDocument
    }
    function jumpOnce() {
        if (jumped || pdfDocument.status !== PdfDocument.Ready || pdfView.width <= 0 || pdfView.height <= 0)
            return
        jumped = true
        let target = page.v.viewerPage
        if (target >= pdfDocument.pageCount || target < 0) {
            target = 0
            warning = desktop.labels.pdfPageUnavailable
        }
        Qt.callLater(function () {
            pdfView.scaleToWidth(pdfView.width, pdfView.height)
            pdfView.goToPage(target)
        })
    }
    Connections { target: pdfDocument; function onStatusChanged() { page.jumpOnce() } }
    Connections { target: pdfView; function onWidthChanged() { page.jumpOnce() } function onHeightChanged() { page.jumpOnce() } }
    Component.onCompleted: jumpOnce()
}
