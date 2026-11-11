import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Dialogs

Item {
    id: dialogs
    required property var theme
    property bool pendingChoice: false
    property var helpReturnFocus: null
    function help() {
        if (clearDialog.visible || diagnosticsDialog.visible || folder.visible || helpDialog.visible)
            return;
        helpReturnFocus = dialogs.Window.window ? dialogs.Window.window.activeFocusItem : null;
        helpDialog.open();
    }
    function choose() {
        if (!desktop.view.initialized) {
            pendingChoice = true;
            desktop.initialize();
        } else
            folder.open();
    }
    function clear() {
        clearDialog.open();
    }
    function diagnostics() {
        diagnosticsDialog.open();
    }
    Connections {
        target: desktop
        function onChanged() {
            if (dialogs.pendingChoice && desktop.view.initialized) {
                dialogs.pendingChoice = false;
                if (!desktop.view.directory)
                    folder.open();
            }
            if (!desktop.view.busy && desktop.view.message && !desktop.view.initialized)
                dialogs.pendingChoice = false;
        }
    }
    FolderDialog {
        id: folder
        title: desktop.labels.choose
        onAccepted: desktop.chooseDirectory(selectedFolder.toString())
    }
    Dialog {
        id: helpDialog
        objectName: "helpDialog"
        title: desktop.labels.help
        modal: true
        anchors.centerIn: parent
        width: Math.min(760, parent.width - 24)
        height: Math.min(620, parent.height - 24)
        palette.window: dialogs.theme.surface
        palette.windowText: dialogs.theme.ink
        onOpened: Qt.callLater(function () { if (helpIndex.itemAt(0)) helpIndex.itemAt(0).forceActiveFocus(); })
        footer: DialogButtonBox {
            Button {
                text: desktop.labels.close
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
        onClosed: {
            if (dialogs.helpReturnFocus && dialogs.helpReturnFocus.visible)
                dialogs.helpReturnFocus.forceActiveFocus();
            dialogs.helpReturnFocus = null;
        }
        contentItem: ScrollView {
            id: helpScroll
            contentWidth: availableWidth
            ColumnLayout {
                width: helpScroll.availableWidth - 16
                spacing: 14
                Flow {
                    Layout.fillWidth: true
                    Layout.preferredHeight: implicitHeight
                    spacing: 6
                    Repeater {
                        id: helpIndex
                        model: [desktop.labels.helpSearchTitle, desktop.labels.helpIndexTitle,
                                desktop.labels.helpReadTitle, desktop.labels.helpKeysTitle]
                        Button {
                            required property int index
                            required property string modelData
                            objectName: "helpSection" + index
                            text: modelData
                            Accessible.name: modelData
                            onClicked: helpScroll.contentItem.contentY = helpSections.itemAt(index).y
                        }
                    }
                }
                Repeater {
                    id: helpSections
                    model: [
                        [desktop.labels.helpSearchTitle, desktop.labels.helpSearchBody],
                        [desktop.labels.helpIndexTitle, desktop.labels.helpIndexBody],
                        [desktop.labels.helpReadTitle, desktop.labels.helpReadBody],
                        [desktop.labels.helpKeysTitle, desktop.labels.helpKeysBody]
                    ]
                    ColumnLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        Label { text: modelData[0]; font.pixelSize: 20; font.weight: Font.DemiBold; color: dialogs.theme.ink; Layout.fillWidth: true; wrapMode: Text.Wrap }
                        Label { text: modelData[1]; color: dialogs.theme.ink; Layout.fillWidth: true; wrapMode: Text.Wrap; textFormat: Text.PlainText }
                    }
                }
            }
        }
    }
    Dialog {
        id: clearDialog
        title: desktop.labels.clearTitle
        palette.window: dialogs.theme.surface
        palette.windowText: dialogs.theme.ink
        background: Rectangle {
            color: dialogs.theme.surface
            radius: 16
            border.color: dialogs.theme.line
        }
        anchors.centerIn: parent
        width: Math.min(520, parent.width - 64)
        modal: true
        contentItem: ColumnLayout {
            Label {
                text: desktop.labels.clearBody
                color: dialogs.theme.ink
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
            RowLayout {
                ActionButton {
                    theme: dialogs.theme
                    text: desktop.labels.back
                    onClicked: clearDialog.close()
                }
                ActionButton {
                    theme: dialogs.theme
                    iconName: "delete"
                    text: desktop.labels.delete
                    enabled: desktop.view.canManage
                    onClicked: {
                        clearDialog.close();
                        desktop.action("clear");
                    }
                }
            }
        }
    }
    Dialog {
        id: diagnosticsDialog
        title: desktop.labels.details
        palette.window: dialogs.theme.surface
        palette.windowText: dialogs.theme.ink
        background: Rectangle {
            color: dialogs.theme.surface
            radius: 16
            border.color: dialogs.theme.line
        }
        anchors.centerIn: parent
        width: Math.min(660, parent.width - 64)
        height: Math.min(480, parent.height - 64)
        modal: true
        standardButtons: Dialog.Close
        contentItem: ScrollView {
            TextArea {
                text: desktop.view.diagnostics
                color: dialogs.theme.ink
                background: Rectangle { color: dialogs.theme.surface }
                readOnly: true
                textFormat: TextEdit.PlainText
                wrapMode: TextEdit.Wrap
                Accessible.name: desktop.labels.details
            }
        }
    }
}
