import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Switch {
    id: control
    required property var theme
    required property var model
    property int currentIndex: 0
    signal activated(int index)
    checked: currentIndex === 1
    implicitHeight: 44
    implicitWidth: 280
    padding: 4
    spacing: 0
    hoverEnabled: true
    Accessible.description: model[currentIndex]
    onClicked: {
        activated(currentIndex === 0 ? 1 : 0);
        checked = Qt.binding(function() { return control.currentIndex === 1; });
    }
    Keys.onLeftPressed: activated(0)
    Keys.onRightPressed: activated(1)
    opacity: enabled ? 1 : 0.5
    indicator: null
    background: Rectangle {
        radius: 12
        color: control.theme.surface
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? control.theme.accent : control.theme.line
    }
    contentItem: RowLayout {
        spacing: 4
        Repeater {
            model: control.model
            delegate: Rectangle {
                required property int index
                required property string modelData
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: 1
                radius: 8
                color: control.currentIndex === index ? control.theme.sage : "transparent"
                Text {
                    anchors.fill: parent
                    anchors.margins: 4
                    text: modelData
                    font: control.font
                    color: control.theme.ink
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        control.forceActiveFocus();
                        control.activated(index);
                    }
                }
            }
        }
    }
}
