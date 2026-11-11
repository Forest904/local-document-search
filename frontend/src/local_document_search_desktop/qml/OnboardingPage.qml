import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Item {
    id: page
    required property var theme
    signal chooseFolder
    property var v: desktop.view
    property var t: desktop.labels
    property int tip: 0
    property var tips: [t.tipPrefix, t.tipPhrase, t.tipFilters, t.tipOpen]
    Timer {
        interval: 8000
        repeat: true
        running: page.visible && (page.v.running || page.v.busy) && !page.v.message
        onTriggered: page.tip = (page.tip + 1) % 4
    }
    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth
        ColumnLayout {
            width: Math.max(0, Math.min(600, page.width - (page.width < 700 ? 16 : 64)))
            x: (page.width - width) / 2
            spacing: 24
            Item {
                Layout.preferredHeight: Math.max(16, page.height * 0.08)
            }
            Brand {
                theme: page.theme
                large: true
                Layout.alignment: Qt.AlignHCenter
            }
            Label {
                text: page.v.running || page.v.busy ? page.t.prepare : page.t.onboardingTitle
                font.pixelSize: 30
                font.weight: Font.DemiBold
                color: page.theme.ink
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
            Label {
                text: page.v.running || page.v.busy ? page.t.building : page.t.onboardingBody
                color: page.theme.muted
                font.pixelSize: 16
                wrapMode: Text.Wrap
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
            }
            Label {
                visible: !page.v.initialized
                text: page.t.privacy
                color: page.theme.muted
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
            ActionButton {
                objectName: "continueButton"
                Component.onCompleted: if (visible)
                    forceActiveFocus()
                iconName: "folder"
                theme: page.theme
                visible: !page.v.initialized
                text: page.v.busy ? page.t.loading : page.t.acceptChoose
                enabled: !page.v.busy && !page.v.closing
                Layout.alignment: Qt.AlignHCenter
                onClicked: {
                    page.chooseFolder();
                }
            }
            Label {
                visible: page.v.directory !== ""
                text: page.v.directory
                textFormat: Text.PlainText
                elide: Text.ElideMiddle
                color: page.theme.muted
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
            }
            ActionButton {
                objectName: "chooseButton"
                iconName: "folder"
                theme: page.theme
                text: page.t.choose
                visible: page.v.initialized && !page.v.running
                enabled: page.v.canManage
                Layout.alignment: Qt.AlignHCenter
                onClicked: page.chooseFolder()
            }
            JobProgress {
                theme: page.theme
                visible: page.v.running || page.v.busy
                Layout.fillWidth: true
            }
            Label {
                text: page.tips[page.tip]
                visible: (page.v.running || page.v.busy) && !page.v.message
                color: page.theme.muted
                wrapMode: Text.Wrap
                Layout.fillWidth: true
                Accessible.ignored: true
            }
            Label {
                visible: page.v.initialized && !page.v.running && page.v.directory !== ""
                text: page.v.status
                color: page.theme.ink
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
            RowLayout {
                visible: page.v.initialized && !page.v.running && page.v.directory !== ""
                ActionButton {
                    theme: page.theme
                    text: page.t.retry
                    enabled: page.v.canManage
                    onClicked: desktop.action("retry")
                }
                ActionButton {
                    theme: page.theme
                    text: page.t.rebuild
                    enabled: page.v.canManage
                    onClicked: desktop.action("rebuild")
                }
                ActionButton {
                    theme: page.theme
                    text: page.t.recover
                    enabled: page.v.canManage
                    onClicked: desktop.action("recover")
                }
            }
        }
    }
}
