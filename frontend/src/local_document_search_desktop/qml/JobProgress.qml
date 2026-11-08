import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

ColumnLayout {
    id: job
    required property var theme
    property var v: desktop.view
    spacing: 16
    Label {
        text: job.v.phase || desktop.labels.loading
        color: job.theme.ink
        font.pixelSize: 18
        Layout.fillWidth: true
        wrapMode: Text.Wrap
    }
    ProgressBar {
        id: bar
        Layout.fillWidth: true
        implicitHeight: 12
        indeterminate: job.v.progress < 0
        value: Math.max(0, job.v.progress)
        Accessible.name: job.v.phase || desktop.labels.loading
        background: Rectangle {
            radius: 6
            color: job.theme.sage
        }
        contentItem: Item {
            clip: true
            Rectangle {
                height: parent.height
                radius: 6
                color: job.theme.accent
                width: bar.indeterminate ? parent.width * 0.25 : parent.width * bar.visualPosition
                property real sweep: 0
                SequentialAnimation on sweep {
                    running: bar.indeterminate && bar.visible
                    loops: Animation.Infinite
                    NumberAnimation {
                        from: 0
                        to: 1
                        duration: 1000
                        easing.type: Easing.InOutSine
                    }
                    NumberAnimation {
                        from: 1
                        to: 0
                        duration: 1000
                        easing.type: Easing.InOutSine
                    }
                }
                x: bar.indeterminate ? sweep * Math.max(0, bar.width * 0.75) : 0
            }
        }
    }
    Label {
        text: job.v.counts + (job.v.progress >= 0 ? "  \u00b7  " + Math.round(job.v.progress * 100) + "%" : "")
        color: job.theme.muted
    }
    ActionButton {
        theme: job.theme
        text: desktop.labels.cancel
        visible: job.v.running
        enabled: job.v.canCancel
        onClicked: desktop.action("cancel")
    }
}
