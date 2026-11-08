import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Dialogs

Item {
    id: dialogs
    required property var theme
    property bool pendingChoice: false
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
