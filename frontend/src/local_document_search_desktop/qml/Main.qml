import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

ApplicationWindow {
    id: root
    objectName: "mainWindow"
    visible: true
    width: Math.min(1280, Screen.desktopAvailableWidth - 32)
    height: Math.min(820, Screen.desktopAvailableHeight - 60)
    minimumWidth: 480
    minimumHeight: 360
    title: root.t.windowTitle
    property var v: desktop.view
    property var t: desktop.labels
    property bool dark: v.theme === "dark"
    Theme {
        id: design
        dark: root.dark
    }
    color: design.backdrop
    font.family: "Segoe UI"
    font.pixelSize: 14
    palette.window: design.backdrop
    palette.windowText: design.ink
    palette.text: design.ink
    palette.placeholderText: design.muted
    palette.base: design.surface
    palette.button: design.surface
    palette.buttonText: design.ink
    palette.highlight: design.accent
    palette.highlightedText: design.backdrop
    palette.mid: design.line
    palette.dark: design.line
    palette.light: design.surface
    onActiveFocusItemChanged: {
        if (content.item && content.item.revealFocus)
            content.item.revealFocus(activeFocusItem);
    }
    onClosing: function (close) {
        close.accepted = v.closed;
        if (!close.accepted) {
            if (v.screen === "viewer" && v.viewerKind === "text" && content.item && content.item.requestLeave)
                content.item.requestLeave("close");
            else desktop.requestClose();
        }
    }
    Connections {
        target: desktop
        function onCloseReady() {
            root.close();
        }
    }
    function focusSearch() {
        if (v.screen === "settings")
            desktop.navigate("back");
        if (content.item && content.item.focusQuery)
            content.item.focusQuery();
    }
    Shortcut {
        sequence: "Ctrl+L"
        onActivated: root.focusSearch()
    }
    Shortcut {
        sequence: "Escape"
        enabled: root.v.screen === "results" || root.v.screen === "viewer"
        onActivated: {
            if (root.v.screen === "viewer" && content.item && content.item.searchOpen)
                content.item.closeFind();
            else if (root.v.screen === "viewer" && root.v.viewerKind === "text" && content.item && content.item.requestLeave)
                content.item.requestLeave("back");
            else
                desktop.navigate(root.v.screen === "viewer" ? "back" : "home");
        }
    }
    Shortcut {
        sequence: "Ctrl+O"
        enabled: v.canManage
        onActivated: {
            if (v.screen === "viewer" && v.viewerKind === "text" && content.item && content.item.requestLeave)
                content.item.requestLeave("choose")
            else dialogs.choose()
        }
    }
    Shortcut {
        sequence: "F1"
        enabled: !(root.v.screen === "viewer" && root.v.viewerKind === "text" && content.item && content.item.confirmExit)
        onActivated: dialogs.help()
    }
    Shortcut {
        sequence: "F5"
        enabled: v.canManage && v.directory !== ""
        onActivated: desktop.action("sync")
    }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: root.v.screen === "viewer" ? 0 : root.width < 700 ? 12 : 24
        spacing: root.height < 500 ? 8 : 16
        RowLayout {
            visible: root.v.screen !== "viewer"
            Layout.fillWidth: true
            Brand {
                theme: design
                resultsHeader: root.v.screen === "results"
                visible: root.v.screen === "results" || root.v.screen === "settings"
            }
            Label {
                visible: root.v.screen !== "results" && root.v.screen !== "settings"
                text: root.t.appName
                color: design.muted
                font.pixelSize: 11
                font.letterSpacing: 1.5
            }
            Item {
                Layout.fillWidth: true
            }
            ActionButton {
                objectName: "helpNavigation"
                theme: design
                text: root.t.help
                onClicked: dialogs.help()
            }
            ActionButton {
                id: settingsNavigation
                objectName: "settingsNavigation"
                theme: design
                iconName: root.v.screen === "settings" ? "back" : "settings"
                text: root.v.screen === "settings" ? root.t.back : root.t.settings
                visible: root.v.initialized && (root.v.screen === "home" || root.v.screen === "settings")
                onClicked: desktop.navigate(root.v.screen === "settings" ? "back" : "settings")
            }
        }
        Loader {
            id: content
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: 0
            Layout.minimumHeight: 0
            Layout.maximumWidth: Math.min(root.width - 2 * (root.v.screen === "viewer" ? 0 : root.width < 700 ? 12 : 24), root.v.screen === "viewer" ? 99999 : root.v.screen === "onboarding" || root.v.screen === "home" ? 1200 : 880)
            Layout.alignment: root.width < 700 ? Qt.AlignLeft : Qt.AlignHCenter
            sourceComponent: root.v.screen === "onboarding" ? onboarding : root.v.screen === "settings" ? settings : root.v.screen === "viewer" ? (root.v.viewerKind === "text" ? textViewer : pdfViewer) : root.v.screen === "results" ? results : home
            onLoaded: Qt.callLater(function () {
                if (root.v.screen === "results" && root.v.focusResultOnReturn && content.item && content.item.focusResult) {
                    content.item.focusResult();
                    desktop.resultFocusRestored();
                } else if (content.item && content.item.focusQuery)
                    content.item.focusQuery();
                else if (root.v.screen === "settings")
                    settingsNavigation.forceActiveFocus();
            })
        }
        Label {
            visible: ((root.v.running || root.v.jobProblem) && root.v.screen !== "onboarding" && root.v.screen !== "settings") || root.v.closing
            text: root.v.status
            color: design.muted
            wrapMode: Text.Wrap
            Layout.fillWidth: true
            Accessible.name: text
        }
        RowLayout {
            visible: root.v.message !== ""
            Layout.fillWidth: true
            Label {
                text: root.v.message
                textFormat: Text.PlainText
                wrapMode: Text.Wrap
                color: design.error
                Layout.fillWidth: true
                Accessible.name: text
            }
            ActionButton {
                theme: design
                text: root.t.retry
                enabled: !root.v.busy && !root.v.closing && (!root.v.initialized || (root.v.canManage && root.v.directory !== ""))
                onClicked: root.v.initialized ? desktop.action("retry") : desktop.initialize()
            }
        }
        ActionButton {
            theme: design
            text: root.t.details
            visible: root.v.screen === "onboarding" && root.v.diagnostics !== ""
            onClicked: dialogs.diagnostics()
        }
    }
    Component {
        id: onboarding
        OnboardingPage {
            theme: design
            onChooseFolder: dialogs.choose()
        }
    }
    Component {
        id: home
        HomePage {
            theme: design
        }
    }
    Component {
        id: results
        ResultsPage {
            theme: design
        }
    }
    Component {
        id: settings
        SettingsPage {
            theme: design
            onChooseFolder: dialogs.choose()
            onClearRequested: dialogs.clear()
            onDiagnosticsRequested: dialogs.diagnostics()
        }
    }
    Component {
        id: pdfViewer
        PdfViewerPage {
            theme: design
            onHelpRequested: dialogs.help()
        }
    }
    Component {
        id: textViewer
        TextViewerPage {
            onChooseRequested: dialogs.choose()
            onHelpRequested: dialogs.help()
            theme: design
        }
    }
    AppDialogs {
        id: dialogs
        anchors.fill: parent
        theme: design
    }
}
