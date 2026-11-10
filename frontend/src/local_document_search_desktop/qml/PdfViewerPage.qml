import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Pdf

ColumnLayout {
    id: page
    required property var theme
    property var v: desktop.view
    spacing: 8

    RowLayout {
        Layout.fillWidth: true
        Button { text: desktop.labels.back; onClicked: desktop.navigate("back") }
        Label { text: page.v.viewerName; color: page.theme.ink; elide: Text.ElideMiddle; Layout.fillWidth: true }
        Label { text: desktop.labels.page + " " + (pdfView.currentPage + 1) + " / " + pdfDocument.pageCount; color: page.theme.ink }
        Button { text: "−"; Accessible.name: desktop.labels.zoomOut; onClicked: pdfView.renderScale *= 0.8 }
        Button { text: "+"; Accessible.name: desktop.labels.zoomIn; onClicked: pdfView.renderScale *= 1.25 }
        Button { text: desktop.labels.fitWidth; onClicked: pdfView.scaleToWidth(pdfView.width, pdfView.height) }
        Button { objectName: "openPdfExternally"; text: desktop.labels.openExternal; onClicked: desktop.openViewerExternally() }
    }
    Label {
        objectName: "pdfWarning"
        visible: pdfDocument.status === PdfDocument.Error || page.warning !== ""
        text: pdfDocument.status === PdfDocument.Error ? desktop.labels.pdfOpenError : page.warning
        color: page.theme.error
        Layout.fillWidth: true
        wrapMode: Text.Wrap
    }
    property string warning: ""
    property bool jumped: false
    PdfDocument { id: pdfDocument; source: page.v.viewerSource }
    PdfMultiPageView {
        id: pdfView
        objectName: "pdfViewer"
        Layout.fillWidth: true
        Layout.fillHeight: true
        document: pdfDocument
    }
    function jumpOnce() {
        if (jumped || pdfDocument.status !== PdfDocument.Ready || pdfView.width <= 0 || pdfView.height <= 0)
            return;
        jumped = true;
        let target = page.v.viewerPage;
        if (target >= pdfDocument.pageCount || target < 0) {
            target = 0;
            warning = desktop.labels.pdfPageUnavailable;
        }
        Qt.callLater(function () {
            pdfView.scaleToWidth(pdfView.width, pdfView.height);
            pdfView.goToPage(target);
        });
    }
    Connections { target: pdfDocument; function onStatusChanged() { page.jumpOnce(); } }
    Connections { target: pdfView; function onWidthChanged() { page.jumpOnce(); } function onHeightChanged() { page.jumpOnce(); } }
    Component.onCompleted: jumpOnce()
}
