import QtQuick
import QtQuick.Controls.Basic

ItemDelegate {
    id: result
    required property var theme
    required property int index
    required property string nameHtml
    required property string pathText
    required property string snippetHtml
    required property string accessibleText
    required property string formatText
    width: ListView.view.width - 8
    height: Math.max(48, content.implicitHeight + 16)
    padding: 8
    Accessible.name: accessibleText
    Accessible.role: Accessible.Link
    highlighted: ListView.isCurrentItem
    background: Rectangle {
        radius: 8
        color: result.hovered ? result.theme.surface : "transparent"
        border.color: result.activeFocus || (result.ListView.view.activeFocus && result.highlighted) ? result.theme.accent : "transparent"
        border.width: 2
    }
    contentItem: Column {
        id: content
        spacing: 4
        Text {
            width: parent.width
            text: result.formatText + "  \u00b7  " + result.pathText
            textFormat: Text.PlainText
            color: result.theme.muted
            font.pixelSize: 12
            elide: Text.ElideMiddle
        }
        Text {
            width: parent.width
            text: result.nameHtml
            textFormat: Text.RichText
            color: result.theme.accent
            font.pixelSize: 18
            wrapMode: Text.Wrap
            font.underline: result.hovered
        }
        Text {
            width: parent.width
            text: result.snippetHtml
            textFormat: Text.RichText
            color: result.theme.ink
            font.pixelSize: 15
            wrapMode: Text.Wrap
            maximumLineCount: 2
            elide: Text.ElideRight
        }
    }
    onClicked: {
        ListView.view.currentIndex = index;
        desktop.openResult(index);
    }
}
