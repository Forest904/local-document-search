import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

ScrollView {
    id: page
    required property var theme
    signal chooseFolder
    signal clearRequested
    signal diagnosticsRequested
    property var v: desktop.view
    property var t: desktop.labels
    contentWidth: availableWidth
    function revealFocus(item) {
        if (!item || !contentItem || !contentItem.contentItem)
            return;
        let ancestor = item;
        while (ancestor && ancestor !== page)
            ancestor = ancestor.parent;
        if (ancestor !== page)
            return;
        const position = item.mapToItem(contentItem.contentItem, 0, 0);
        const top = contentItem.contentY;
        const bottom = top + availableHeight;
        if (position.y < top + 12)
            contentItem.contentY = Math.max(0, position.y - 12);
        else if (position.y + item.height > bottom - 12)
            contentItem.contentY = Math.min(Math.max(0, contentHeight - availableHeight), position.y + item.height - availableHeight + 12);
    }
    function applyOptions(orderIndex) {
        let formats = [];
        if (txt.checked)
            formats.push("txt");
        if (md.checked)
            formats.push("md");
        if (pdf.checked)
            formats.push("pdf");
        desktop.setOptions(["both", "filename", "content"][field.currentIndex], formats, folder.text, (orderIndex === undefined ? order.currentIndex : orderIndex) === 0 ? "relevance" : "path");
    }
    ColumnLayout {
        width: page.availableWidth - 24
        spacing: 16
        Label {
            text: page.t.settings
            font.pixelSize: 32
            font.weight: Font.DemiBold
            color: page.theme.ink
        }
        Label {
            text: page.t.searchSettings
            font.pixelSize: 22
            color: page.theme.ink
            Layout.topMargin: 16
        }
        Label {
            text: page.t.sessionFilters
            color: page.theme.muted
            wrapMode: Text.Wrap
            Layout.fillWidth: true
        }
        GridLayout {
            Layout.fillWidth: true
            columns: 2
            columnSpacing: 32
            rowSpacing: 16
            Label {
                text: page.t.field
                color: page.theme.ink
            }
            OptionSelect {
                id: field
                theme: page.theme
                objectName: "field"
                model: [page.t.both, page.t.filename, page.t.content]
                currentIndex: ["both", "filename", "content"].indexOf(page.v.field)
                Accessible.name: page.t.field
                Layout.fillWidth: true
                onActivated: page.applyOptions()
            }
            Label {
                text: page.t.formats
                color: page.theme.ink
            }
            RowLayout {
                CheckBox {
                    id: txt
                    text: "TXT"
                    palette.windowText: page.theme.ink
                    checked: page.v.formats.indexOf("txt") >= 0
                    enabled: !checked || md.checked || pdf.checked
                    onClicked: page.applyOptions()
                }
                CheckBox {
                    id: md
                    text: "MD"
                    palette.windowText: page.theme.ink
                    checked: page.v.formats.indexOf("md") >= 0
                    enabled: !checked || txt.checked || pdf.checked
                    onClicked: page.applyOptions()
                }
                CheckBox {
                    id: pdf
                    text: "PDF"
                    palette.windowText: page.theme.ink
                    checked: page.v.formats.indexOf("pdf") >= 0
                    enabled: !checked || txt.checked || md.checked
                    onClicked: page.applyOptions()
                }
            }
            Label {
                text: page.t.folder
                color: page.theme.ink
            }
            TextField {
                id: folder
                implicitHeight: 44
                leftPadding: 16
                rightPadding: 16
                background: Rectangle {
                    radius: 12
                    color: page.theme.surface
                    border.width: folder.activeFocus ? 2 : 1
                    border.color: folder.activeFocus ? page.theme.accent : page.theme.line
                }
                objectName: "folderFilter"
                text: page.v.folder
                placeholderText: page.t.folder
                color: page.theme.ink
                placeholderTextColor: page.theme.muted
                Accessible.name: page.t.folder
                Layout.fillWidth: true
                onEditingFinished: if (text !== page.v.folder)
                    page.applyOptions()
            }
            Label {
                text: page.t.order
                color: page.theme.ink
            }
            BinarySelect {
                id: order
                objectName: "order"
                theme: page.theme
                model: [page.t.relevance, page.t.path]
                currentIndex: page.v.order === "relevance" ? 0 : 1
                Accessible.name: page.t.order
                Layout.fillWidth: true
                onActivated: function(index) { page.applyOptions(index); }
            }
        }
        ActionButton {
            theme: page.theme
            text: page.t.resetFilters
            onClicked: desktop.resetOptions()
        }
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: page.theme.line
            Layout.topMargin: 12
        }
        Label {
            text: page.t.indexSettings
            font.pixelSize: 22
            color: page.theme.ink
        }
        Label {
            text: page.v.directory || page.t.none
            textFormat: Text.PlainText
            wrapMode: Text.Wrap
            color: page.theme.muted
            Layout.fillWidth: true
        }
        Flow {
            Layout.fillWidth: true
            spacing: 12
            ActionButton {
                theme: page.theme
                iconName: "folder"
                text: page.t.choose
                enabled: page.v.canManage
                onClicked: page.chooseFolder()
            }
            ActionButton {
                theme: page.theme
                iconName: "sync"
                text: page.t.sync
                enabled: page.v.canManage && page.v.directory !== ""
                onClicked: desktop.action("sync")
            }
            ActionButton {
                theme: page.theme
                text: page.t.rebuild
                enabled: page.v.canManage && page.v.directory !== ""
                onClicked: desktop.action("rebuild")
            }
            ActionButton {
                theme: page.theme
                text: page.t.recover
                enabled: page.v.canManage && page.v.directory !== ""
                onClicked: desktop.action("recover")
            }
        }
        Label {
            text: page.v.status
            color: page.theme.muted
            wrapMode: Text.Wrap
            Layout.fillWidth: true
        }
        JobProgress {
            theme: page.theme
            visible: page.v.running
            Layout.fillWidth: true
        }
        ActionButton {
            theme: page.theme
            text: page.t.details
            visible: page.v.diagnostics !== ""
            onClicked: page.diagnosticsRequested()
        }
        ActionButton {
            theme: page.theme
            text: page.t.clear
            enabled: page.v.canManage
            onClicked: page.clearRequested()
        }
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: page.theme.line
            Layout.topMargin: 12
        }
        Label {
            text: page.t.appearance
            font.pixelSize: 22
            color: page.theme.ink
        }
        GridLayout {
            Layout.fillWidth: true
            columns: 2
            columnSpacing: 32
            rowSpacing: 16
            Label {
                text: page.t.language
                color: page.theme.ink
            }
            BinarySelect {
                theme: page.theme
                objectName: "language"
                model: ["Italiano", "English"]
                currentIndex: page.v.language === "it" ? 0 : 1
                enabled: page.v.ready
                Accessible.name: page.t.language
                Layout.fillWidth: true
                onActivated: function(index) { desktop.savePreferences(index === 0 ? "it" : "en", page.v.theme); }
            }
            Label {
                text: page.t.theme
                color: page.theme.ink
            }
            BinarySelect {
                theme: page.theme
                objectName: "theme"
                model: [page.t.light, page.t.dark]
                currentIndex: page.v.theme === "light" ? 0 : 1
                enabled: page.v.ready
                Accessible.name: page.t.theme
                Layout.fillWidth: true
                onActivated: function(index) { desktop.savePreferences(page.v.language, index === 0 ? "light" : "dark"); }
            }
        }
        Item {
            Layout.preferredHeight: 32
        }
    }
}
