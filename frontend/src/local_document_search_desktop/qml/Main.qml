import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

ApplicationWindow {
    id: root
    objectName: "mainWindow"
    visible: true
    width: Math.min(1280, Screen.desktopAvailableWidth - 32)
    height: Math.min(820, Screen.desktopAvailableHeight - 60)
    minimumWidth: 900
    minimumHeight: 640
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
        if (!close.accepted)
            desktop.requestClose();
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
        enabled: root.v.screen === "results"
        onActivated: desktop.navigate("home")
    }
    Shortcut {
        sequence: "Ctrl+O"
        enabled: v.canManage
        onActivated: dialogs.choose()
    }
    Shortcut {
        sequence: "F5"
        enabled: v.canManage && v.directory !== ""
        onActivated: desktop.action("sync")
    }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16
        RowLayout {
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
            Layout.maximumWidth: root.v.screen === "onboarding" || root.v.screen === "home" ? 1200 : 880
            Layout.alignment: Qt.AlignHCenter
            sourceComponent: root.v.screen === "onboarding" ? onboarding : root.v.screen === "settings" ? settings : root.v.screen === "results" ? results : home
            onLoaded: Qt.callLater(function () {
                if (content.item && content.item.focusQuery)
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
    AppDialogs {
        id: dialogs
        anchors.fill: parent
        theme: design
    }
}
