pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.Ui
import qs.Commons
import qs.Commons as Commons
import "UiRules.js" as Rules

Panel {
    id: root
    moduleName: "phi0x.sennheiser"
    ipcTarget: "phi0x.sennheiser"
    property var snapshot: ({
            dongle: {},
            headphones: {},
            devices: []
        })
    readonly property var dongle: snapshot.dongle || ({})
    readonly property var hp: snapshot.headphones || ({})
    readonly property var values: hp.values || ({})
    readonly property bool blockingBusy: !!snapshot.busy && snapshot.operation !== "setting"
    property int broadcastRevision: snapshot.broadcast_revision || 0
    onBroadcastRevisionChanged: {
        if (snapshot.broadcast) {
            broadcastName.text = snapshot.broadcast.name;
            broadcastAudience.currentIndex = snapshot.broadcast.public ? 1 : 0;
            broadcastQuality.currentIndex = snapshot.broadcast.quality;
            broadcastEncrypted.checked = snapshot.broadcast.encrypted;
            broadcastPassword.clear();
        }
    }
    property int graphicRevision: snapshot.graphic_revision || 0
    onGraphicRevisionChanged: {
        graphicLoader.reloading = true;
        Qt.callLater(function () {
            graphicLoader.reloading = false;
        });
    }
    property int eqRevision: snapshot.peq_revision || 0
    onEqRevisionChanged: {
        eqLoader.reloading = true;
        Qt.callLater(function () {
            eqLoader.reloading = false;
        });
    }
    property string expandedHelp: ""
    property string tab: "dongle"
    onTabChanged: Qt.callLater(function () {
        if (settingsScroll.contentItem && settingsScroll.contentItem.contentY !== undefined)
            settingsScroll.contentItem.contentY = 0;
    })
    property bool started: false
    property string workerError: ""
    implicitWidth: icon.implicitWidth
    implicitHeight: icon.implicitHeight
    onOpenedChanged: {
        if (opened && !started) {
            started = true;
            worker.running = true;
        } else if (opened)
            send({
                action: "refresh"
            });
    }
    function send(request) {
        if (worker.running && !snapshot.busy) {
            worker.write(JSON.stringify(request) + "\n");
            workerError = "";
            return true;
        }
        return false;
    }
    function change(key, value) {
        send({
            action: "setting",
            key: key,
            value: value
        });
    }
    Process {
        id: worker
        command: ["/usr/bin/python", "-B", Quickshell.env("HOME") + "/.config/omarchy/plugins/phi0x.sennheiser/backend/client.py"]
        stdinEnabled: true
        stdout: SplitParser {
            onRead: data => {
                try {
                    root.snapshot = JSON.parse(data);
                } catch (e) {
                    root.workerError = "Could not read controller response";
                }
            }
        }
        stderr: SplitParser {
            onRead: data => {
                root.workerError = data;
            }
        }
        onExited: (code, status) => {
            root.started = false;
            root.snapshot = {
                dongle: {},
                headphones: {},
                devices: []
            };
            root.workerError = "Controller stopped (" + code + "). Close and reopen to retry.";
        }
    }
    IpcHandler {
        target: "sennheiser-control"
        function status(): string {
            return JSON.stringify(root.snapshot);
        }
        function showTab(name: string): void {
            root.tab = name;
            root.open();
        }
        function explain(topic: string): void {
            root.tab = ["eq", "pregain", "filter", "frequency", "gain", "q"].indexOf(topic) >= 0 ? "eq" : (["audio_mode", "transport", "codec"].indexOf(topic) >= 0 ? "dongle" : "headphones");
            root.expandedHelp = topic;
            root.open();
        }
    }
    BarIconButton {
        id: icon
        anchors.fill: parent
        bar: root.bar
        text: "󰋋"
        active: root.opened
        tooltipText: "Sennheiser · " + (root.dongle.codec || "HDB 630 / BTD 700")
        onPressed: root.toggle()
    }
    component Copy: Text {
        color: Commons.Color.foreground
        font.family: Style.font.family
        font.pixelSize: 14
        textFormat: Text.PlainText
        wrapMode: Text.WordWrap
        Layout.fillWidth: true
    }
    component Action: Controls.Button {
        id: actionButton
        Layout.fillWidth: true
        implicitHeight: 38
        enabled: !root.blockingBusy
        opacity: enabled ? 1 : 0.5
        background: Rectangle {
            radius: 4
            color: actionButton.down || actionButton.checked ? Qt.alpha(Commons.Color.accent, 0.24) : Qt.alpha(Commons.Color.foreground, actionButton.hovered ? 0.14 : 0.07)
            border.width: actionButton.activeFocus ? 1 : 0
            border.color: Commons.Color.accent
        }
        contentItem: Text {
            text: actionButton.text
            textFormat: Text.PlainText
            color: Commons.Color.foreground
            font.family: Style.font.family
            font.pixelSize: 14
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }
    component Choice: Controls.ComboBox {
        id: choice
        Layout.fillWidth: true
        implicitHeight: 38
        palette.text: Commons.Color.foreground
        palette.buttonText: Commons.Color.foreground
        palette.base: Commons.Color.popups.background
        palette.window: Commons.Color.popups.background
        palette.highlight: Commons.Color.accent
        background: Rectangle {
            radius: 4
            color: Qt.alpha(Commons.Color.foreground, 0.05)
            border.width: 1
            border.color: Qt.alpha(Commons.Color.foreground, choice.activeFocus ? 0.5 : 0.15)
        }
        contentItem: Text {
            text: choice.displayText
            textFormat: Text.PlainText
            color: Commons.Color.foreground
            font.family: Style.font.family
            font.pixelSize: 14
            leftPadding: 10
            rightPadding: 22
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
    }
    component InfoButton: Controls.Button {
        id: infoButton
        property string topic
        property string helpId: topic
        implicitWidth: 24
        implicitHeight: 24
        Layout.preferredWidth: 24
        Layout.preferredHeight: 24
        Accessible.name: "Explain " + topic.replace(/_/g, " ")
        checkable: true
        checked: root.expandedHelp === helpId
        onClicked: root.expandedHelp = checked ? helpId : ""
        background: Rectangle {
            radius: 12
            color: Qt.alpha(Commons.Color.accent, infoButton.checked || infoButton.hovered ? .22 : .07)
            border.width: 1
            border.color: Qt.alpha(Commons.Color.foreground, infoButton.activeFocus ? .8 : .2)
        }
        contentItem: Text {
            text: "i"
            color: Commons.Color.foreground
            font.pixelSize: 14
            font.italic: true
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }
    component HelpLabel: ColumnLayout {
        id: helpLabel
        property string title
        property string topic
        property string helpId: topic
        property real level: 0
        Layout.fillWidth: true
        spacing: 8
        RowLayout {
            Layout.fillWidth: true
            Copy {
                text: helpLabel.title
                font.bold: true
            }
            InfoButton {
                topic: helpLabel.topic
                helpId: helpLabel.helpId
            }
        }
        HelpCard {
            visible: root.expandedHelp === helpLabel.helpId
            topic: helpLabel.topic
            level: helpLabel.level
        }
    }
    component Setting: ColumnLayout {
        id: settingRow
        property var availability: Rules.dependency(settingKey, root.values)
        property string title
        property string settingKey
        Layout.topMargin: 2
        Layout.bottomMargin: 2
        Layout.fillWidth: true
        spacing: 8
        visible: root.values[settingKey] !== undefined
        RowLayout {
            Layout.fillWidth: true
            Copy {
                text: settingRow.title
                opacity: settingRow.availability.available ? 1 : .5
            }
            InfoButton {
                topic: settingRow.settingKey
            }
            Controls.Switch {
                checked: !!root.values[settingRow.settingKey]
                enabled: !root.blockingBusy && settingRow.availability.available
                onClicked: root.change(settingRow.settingKey, checked ? 1 : 0)
            }
        }
        Copy {
            visible: !settingRow.availability.available
            text: settingRow.availability.reason
            font.pixelSize: 12
            opacity: .65
        }
        HelpCard {
            visible: root.expandedHelp === settingRow.settingKey
            topic: settingRow.settingKey
        }
    }
    component ValueSetting: ColumnLayout {
        id: valueSetting
        property var availability: Rules.dependency(settingKey, root.values)
        property string title
        property string settingKey
        property string helpTopic: settingKey === "audio_mode" ? "headphone_audio_mode" : settingKey
        property var choices
        Layout.fillWidth: true
        spacing: 10
        visible: root.values[settingKey] !== undefined
        HelpLabel {
            title: valueSetting.title
            topic: valueSetting.helpTopic
        }
        Choice {
            model: valueSetting.choices
            textRole: "name"
            currentIndex: valueSetting.choices.findIndex(function (item) {
                return item.value === root.values[valueSetting.settingKey];
            })
            enabled: !root.blockingBusy && valueSetting.availability.available
            opacity: enabled ? 1 : .4
            onActivated: root.change(valueSetting.settingKey, valueSetting.choices[currentIndex].value)
        }
        Copy {
            visible: !valueSetting.availability.available
            text: valueSetting.availability.reason
            font.pixelSize: 12
            opacity: .65
        }
    }
    component FirmwareStatus: Section {
        id: firmwareStatus
        property string deviceKey
        property string installed
        property string officialUrl
        property string officialLabel
        readonly property var result: root.snapshot.firmware_check ? root.snapshot.firmware_check.devices[deviceKey] : null
        Copy {
            text: "Installed: " + (firmwareStatus.installed || "Connect the device to read its version")
        }
        Copy {
            visible: !!firmwareStatus.result
            text: "Latest in catalog: " + (firmwareStatus.result ? firmwareStatus.result.latest || "Unavailable" : "")
        }
        Copy {
            visible: !!firmwareStatus.result
            text: {
                if (!firmwareStatus.result)
                    return "";
                let status = firmwareStatus.result.status;
                if (status === "up-to-date")
                    return "Last check: up to date.";
                if (status === "update-available")
                    return "Last check: a newer firmware is available. Install it using the official updater.";
                if (status === "newer-than-catalog")
                    return "Installed version is newer than the catalog. No downgrade is offered.";
                if (status === "connect-device")
                    return "Connect the device, then check again to compare versions.";
                return firmwareStatus.result.error || "Update status could not be verified.";
            }
        }
        Action {
            text: firmwareStatus.officialLabel
            onClicked: Qt.openUrlExternally(firmwareStatus.officialUrl)
        }
    }
    component Divider: Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 1
        Layout.topMargin: 4
        Layout.bottomMargin: 4
        color: Qt.alpha(Commons.Color.foreground, .12)
    }
    KeyboardPanel {
        id: popup
        bar: root.bar
        owner: root
        anchorItem: icon
        open: root.opened
        contentWidth: fittedContentWidth(Style.space(500))
        contentHeight: fittedContentHeight(panelHeader.implicitHeight + panelContent.implicitHeight + panelFooter.implicitHeight + 36, Style.space(760))
        ColumnLayout {
            anchors.fill: parent
            spacing: 16
            ColumnLayout {
                id: panelHeader
                Layout.fillWidth: true
                spacing: 12
                Copy {
                    text: "Sennheiser"
                    font.pixelSize: 22
                    font.bold: true
                }
                Copy {
                    text: "HDB 630  /  BTD 700"
                    opacity: .6
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Action {
                        text: "Dongle"
                        checked: root.tab === "dongle"
                        checkable: true
                        onClicked: root.tab = "dongle"
                    }
                    Action {
                        text: "Headphones"
                        checked: root.tab === "headphones"
                        checkable: true
                        onClicked: root.tab = "headphones"
                    }
                    Action {
                        text: "EQ"
                        checked: root.tab === "eq"
                        checkable: true
                        onClicked: root.tab = "eq"
                    }
                    Action {
                        text: "Updates"
                        checked: root.tab === "updates"
                        checkable: true
                        onClicked: root.tab = "updates"
                    }
                }
                Divider {}
            }
            Controls.ScrollView {
                id: settingsScroll
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 80
                clip: true
                // Keep a permanent gutter, even when the scrollbar fades out.
                rightPadding: Math.max(Style.space(12), verticalScroll.implicitWidth) + Style.space(8)
                contentWidth: availableWidth
                contentHeight: panelContent.implicitHeight
                Controls.ScrollBar.horizontal.policy: Controls.ScrollBar.AlwaysOff
                Controls.ScrollBar.vertical: Controls.ScrollBar {
                    id: verticalScroll
                    policy: Controls.ScrollBar.AsNeeded
                    active: size < 1
                }
                ColumnLayout {
                    id: panelContent
                    width: settingsScroll.availableWidth
                    spacing: 20
                    Copy {
                        visible: !!root.workerError
                        text: root.workerError
                    }
                    Copy {
                        visible: !!root.snapshot.message
                        text: root.snapshot.message || ""
                        opacity: .8
                    }
                    Copy {
                        visible: root.blockingBusy
                        text: "Working…"
                    }
                    ColumnLayout {
                        visible: root.tab === "dongle"
                        Layout.fillWidth: true
                        spacing: 20
                        Section {
                            title: "Link status"
                            Copy {
                                text: root.dongle.connected ? root.dongle.state : (root.dongle.error || "Reading dongle…")
                            }
                            Copy {
                                visible: !!root.dongle.connected
                                text: (root.dongle.codec || "") + "\n" + (root.dongle.quality || "") + "\nFirmware " + (root.dongle.firmware || "")
                            }
                        }
                        Section {
                            title: "Playback"
                            subtitle: "Choose quality, latency and connection type"
                            visible: !!root.dongle.connected
                            HelpLabel {
                                title: "Audio mode"
                                topic: "audio_mode"
                            }
                            Choice {
                                id: audioMode
                                Layout.fillWidth: true
                                model: ["High quality", "Low latency", "Broadcast"]
                                currentIndex: root.dongle.mode === undefined ? 0 : root.dongle.mode
                            }
                            HelpLabel {
                                title: "Connection type"
                                topic: "transport"
                            }
                            Choice {
                                id: transport
                                Layout.fillWidth: true
                                model: ["Bluetooth Classic", "LE Audio", "Multipoint"]
                                currentIndex: Math.max(0, (root.dongle.transport || 1) - 1)
                            }
                            Action {
                                text: "Apply audio mode"
                                onClicked: root.send({
                                    action: "mode",
                                    mode: audioMode.currentIndex,
                                    transport: transport.currentIndex + 1
                                })
                            }
                        }
                        Section {
                            title: "Wireless encoding"
                            subtitle: "Choose how audio is sent to the headphones"
                            visible: !!root.dongle.connected
                            HelpLabel {
                                title: "Codec preference"
                                topic: "codec"
                            }
                            Copy {
                                text: "Changing the codec or audio mode may briefly interrupt playback."
                                opacity: .65
                            }
                            Choice {
                                id: codecs
                                Layout.fillWidth: true
                                textRole: "name"
                                model: {
                                    let list = [
                                        {
                                            name: "Automatic (all supported)",
                                            mask: root.dongle.supported || 1
                                        }
                                    ];
                                    let names = ["SBC", "aptX", "aptX Adaptive", "aptX Lossless", "aptX Lite", "LC3"];
                                    for (let i = 0; i < names.length; ++i)
                                        if ((root.dongle.supported || 0) & (1 << i))
                                            list.push({
                                                name: names[i],
                                                mask: 1 << i
                                            });
                                    return list;
                                }
                            }
                            Action {
                                text: "Apply codec preference"
                                onClicked: root.send({
                                    action: "codec",
                                    mask: codecs.model[codecs.currentIndex].mask
                                })
                            }
                        }
                        Section {
                            title: "Auracast broadcast"
                            subtitle: "Configure a broadcast before selecting Broadcast audio mode"
                            visible: !!root.dongle.connected
                            HelpLabel {
                                title: "Broadcast settings"
                                topic: "broadcast"
                            }
                            Action {
                                text: "Read broadcast settings"
                                onClicked: root.send({
                                    action: "broadcast_read"
                                })
                            }
                            ColumnLayout {
                                visible: !!root.snapshot.broadcast
                                Layout.fillWidth: true
                                spacing: 14
                                Copy {
                                    text: "Broadcast name"
                                }
                                Controls.TextField {
                                    id: broadcastName
                                    Layout.fillWidth: true
                                    text: root.snapshot.broadcast ? root.snapshot.broadcast.name : ""
                                    placeholderText: "Name shown to receivers"
                                }
                                Copy {
                                    text: "Broadcast visibility"
                                }
                                Choice {
                                    id: broadcastAudience
                                    model: ["Private / off", "Public"]
                                    currentIndex: root.snapshot.broadcast && root.snapshot.broadcast.public ? 1 : 0
                                }
                                Copy {
                                    text: "Broadcast quality"
                                }
                                Choice {
                                    id: broadcastQuality
                                    model: ["Standard · 16 kHz", "Standard · 24 kHz", "High"]
                                    currentIndex: root.snapshot.broadcast ? root.snapshot.broadcast.quality : 2
                                }
                                RowLayout {
                                    Layout.fillWidth: true
                                    Copy {
                                        text: "Password protection"
                                    }
                                    Controls.Switch {
                                        id: broadcastEncrypted
                                        checked: !!root.snapshot.broadcast && root.snapshot.broadcast.encrypted
                                    }
                                }
                                Controls.TextField {
                                    id: broadcastPassword
                                    Layout.fillWidth: true
                                    visible: broadcastEncrypted.checked
                                    echoMode: TextInput.Password
                                    placeholderText: root.snapshot.broadcast && root.snapshot.broadcast.encrypted ? "Leave blank to keep the current password" : "Enter 1–16 UTF-8 bytes"
                                }
                                Action {
                                    text: "Save broadcast settings"
                                    onClicked: {
                                        let request = {
                                            action: "broadcast_write",
                                            name: broadcastName.text,
                                            public: broadcastAudience.currentIndex === 1,
                                            quality: broadcastQuality.currentIndex,
                                            encrypted: broadcastEncrypted.checked
                                        };
                                        if (broadcastPassword.text.length)
                                            request.password = broadcastPassword.text;
                                        if (root.send(request))
                                            broadcastPassword.clear();
                                    }
                                }
                            }
                        }
                    }
                    ColumnLayout {
                        visible: root.tab === "headphones"
                        Layout.fillWidth: true
                        spacing: 20
                        Section {
                            title: "Connection"
                            HelpLabel {
                                title: "Headphone connection"
                                topic: "connection"
                            }
                            Copy {
                                visible: !root.hp.connected
                                text: root.hp.reconnecting ? "Paired headphones will reconnect automatically when available." : "Pair with the computer for settings; keep the dongle for audio."
                                opacity: .7
                            }
                            Copy {
                                visible: !!root.hp.error
                                text: root.hp.error || ""
                            }
                            Action {
                                visible: !root.hp.connected
                                text: "Search for HDB 630"
                                onClicked: root.send({
                                    action: "scan"
                                })
                            }
                            Repeater {
                                model: root.hp.connected ? [] : (root.snapshot.devices || [])
                                Action {
                                    required property var modelData
                                    text: (modelData.paired ? "Connect " : "Pair & connect ") + modelData.name
                                    onClicked: root.send({
                                        action: "connect",
                                        address: modelData.address
                                    })
                                }
                            }
                            Copy {
                                visible: !!root.hp.connected
                                text: (root.values.battery === undefined ? "" : root.values.battery + "% battery") + (root.values.charging === 1 ? " · Charging" : "") + " · Firmware " + (root.values.firmware || "")
                            }
                            Action {
                                visible: !!root.hp.connected || !!root.hp.reconnecting
                                text: root.hp.connected ? "Disconnect controls" : "Stop reconnecting"
                                onClicked: root.send({
                                    action: "disconnect"
                                })
                            }
                        }
                        ColumnLayout {
                            visible: !!root.hp.connected
                            Layout.fillWidth: true
                            spacing: 20
                            Section {
                                title: "Noise control"
                                subtitle: "Balance quiet listening with awareness of your surroundings"
                                Setting {
                                    title: "Noise cancellation"
                                    settingKey: "anc"
                                }
                                Setting {
                                    title: "Adaptive ANC"
                                    settingKey: "adaptive"
                                }
                                ValueSetting {
                                    title: "Wind noise reduction"
                                    settingKey: "anti_wind"
                                    choices: [
                                        {
                                            name: "Off",
                                            value: 0
                                        },
                                        {
                                            name: "Automatic",
                                            value: 2
                                        },
                                        {
                                            name: "Maximum",
                                            value: 1
                                        }
                                    ]
                                }
                                Divider {}
                                HelpLabel {
                                    title: !root.values.anc ? "Transparency · inactive" : root.values.adaptive ? "Transparency · automatic" : "Transparency · " + Math.round(transparency.value) + "%"
                                    topic: "transparency"
                                    level: transparency.value
                                }
                                Controls.Slider {
                                    id: transparency
                                    property int pendingValue: -1
                                    property bool inFlight: false
                                    Layout.fillWidth: true
                                    from: 0
                                    to: 100
                                    stepSize: 1
                                    enabled: !root.blockingBusy && !!root.values.anc && !root.values.adaptive
                                    opacity: enabled ? 1 : .4
                                    onEnabledChanged: {
                                        if (!enabled) {
                                            pendingValue = -1;
                                            transparencyWrite.stop();
                                        }
                                    }
                                    // Polls must not move the handle during a drag or pending write.
                                    Binding {
                                        target: transparency
                                        property: "value"
                                        value: root.values.transparency || 0
                                        when: !transparency.pressed && transparency.pendingValue < 0 && !transparency.inFlight
                                        restoreMode: Binding.RestoreNone
                                    }
                                    onMoved: {
                                        pendingValue = Math.round(value);
                                        if (!pressed)
                                            transparencyWrite.restart();
                                    }
                                    onPressedChanged: if (enabled && !pressed && pendingValue >= 0)
                                        transparencyWrite.restart()
                                    Connections {
                                        target: root
                                        function onSnapshotChanged() {
                                            if (!root.snapshot.busy)
                                                transparency.inFlight = false;
                                        }
                                    }
                                    Timer {
                                        id: transparencyWrite
                                        interval: 120
                                        onTriggered: {
                                            if (!transparency.enabled || transparency.pressed || transparency.pendingValue < 0)
                                                return;
                                            if (root.snapshot.busy) {
                                                restart();
                                                return;
                                            }
                                            if (root.send({
                                                action: "setting",
                                                key: "transparency",
                                                value: transparency.pendingValue
                                            })) {
                                                transparency.inFlight = true;
                                                transparency.pendingValue = -1;
                                            }
                                        }
                                    }
                                }
                                RowLayout {
                                    Layout.fillWidth: true
                                    Copy {
                                        text: "More cancellation"
                                        font.pixelSize: 11
                                        opacity: .65
                                    }
                                    Copy {
                                        text: "Hear surroundings"
                                        font.pixelSize: 11
                                        opacity: .65
                                        horizontalAlignment: Text.AlignRight
                                    }
                                }
                                Copy {
                                    visible: !root.values.anc || !!root.values.adaptive
                                    text: !root.values.anc ? "Enable Noise cancellation to use the manual balance." : "Adaptive ANC manages the balance. Turn it off for manual control."
                                    font.pixelSize: 11
                                    opacity: .7
                                }
                            }
                            Section {
                                title: "Stereo image"
                                subtitle: "Adjust how left and right channels blend"
                                HelpLabel {
                                    title: "Crossfeed"
                                    topic: "crossfeed"
                                    level: root.values.crossfeed === undefined ? 2 : root.values.crossfeed
                                }
                                Choice {
                                    Layout.fillWidth: true
                                    model: ["Low", "High", "Off"]
                                    currentIndex: root.values.crossfeed === undefined ? 2 : root.values.crossfeed
                                    enabled: !root.blockingBusy
                                    onActivated: root.change("crossfeed", currentIndex)
                                }
                            }
                            Section {
                                title: "Wear detection"
                                subtitle: "Control what happens when you put the headphones on or take them off"
                                Setting {
                                    title: "On-head detection"
                                    settingKey: "on_head"
                                }
                                Setting {
                                    title: "Smart pause"
                                    settingKey: "smart_pause"
                                }
                            }
                            Section {
                                title: "Calls"
                                subtitle: "Call handling and hearing your own voice"
                                Setting {
                                    title: "Auto-answer calls"
                                    settingKey: "auto_answer"
                                }
                                Setting {
                                    title: "Comfort call"
                                    settingKey: "comfort_call"
                                }
                                ValueSetting {
                                    title: "Call transparency / sidetone"
                                    settingKey: "sidetone"
                                    choices: [
                                        {
                                            name: "Off",
                                            value: 0
                                        },
                                        {
                                            name: "Level 1",
                                            value: 1
                                        },
                                        {
                                            name: "Level 2",
                                            value: 2
                                        },
                                        {
                                            name: "Level 3",
                                            value: 3
                                        },
                                        {
                                            name: "Level 4",
                                            value: 4
                                        }
                                    ]
                                }
                                Setting {
                                    title: "Pause music for call transparency"
                                    settingKey: "auto_pause"
                                }
                            }
                            Section {
                                title: "Power"
                                ValueSetting {
                                    title: "Automatic power off"
                                    settingKey: "auto_off"
                                    choices: [
                                        {
                                            name: "Never",
                                            value: 0
                                        },
                                        {
                                            name: "After 15 minutes",
                                            value: 900
                                        },
                                        {
                                            name: "After 30 minutes",
                                            value: 1800
                                        },
                                        {
                                            name: "After 60 minutes",
                                            value: 3600
                                        }
                                    ]
                                }
                            }
                            Section {
                                title: "Wireless resolution"
                                visible: root.values.compatibility !== undefined
                                HelpLabel {
                                    title: "Resolution preference"
                                    topic: "resolution"
                                }
                                Choice {
                                    id: resolution
                                    model: ["High resolution", "Standard compatibility"]
                                    currentIndex: root.values.compatibility || 0
                                }
                                Copy {
                                    text: "Applying a different preference restarts the headphones and briefly interrupts audio."
                                    opacity: .7
                                }
                                Action {
                                    text: "Apply and restart headphones"
                                    onClicked: root.send({
                                        action: "resolution",
                                        high_resolution: resolution.currentIndex === 0
                                    })
                                }
                            }
                            Section {
                                title: "Paired devices"
                                subtitle: "Read-only list of devices remembered by the headphones"
                                Action {
                                    text: "Read paired devices"
                                    onClicked: root.send({
                                        action: "paired_read"
                                    })
                                }
                                Repeater {
                                    model: root.snapshot.paired_devices || []
                                    Copy {
                                        required property var modelData
                                        text: (modelData.name || "Unnamed device") + " · " + (modelData.connected ? "Connected" : "Disconnected") + (modelData.own ? " · This computer" : "")
                                    }
                                }
                            }
                            Section {
                                title: "Advanced"
                                subtitle: "Experimental firmware setting"
                                Setting {
                                    title: "Comfort ANC"
                                    settingKey: "comfort"
                                }
                            }
                        }
                    }
                    ColumnLayout {
                        visible: root.tab === "eq"
                        Layout.fillWidth: true
                        spacing: 20
                        Section {
                            title: "Equalizer"
                            subtitle: "Read your current settings before editing"
                            HelpLabel {
                                title: "Parametric EQ"
                                topic: "eq"
                            }
                            Copy {
                                text: root.hp.connected ? "Five-band parametric EQ stored on your headphones." : "Connect headphones in the Headphones tab to edit EQ."
                            }
                            Action {
                                visible: !!root.hp.connected
                                text: "Read EQ from headphones"
                                onClicked: root.send({
                                    action: "peq_read"
                                })
                            }
                        }
                        Section {
                            title: "Sound processing"
                            visible: !!root.hp.connected
                            ValueSetting {
                                title: "Audio processing mode"
                                settingKey: "audio_mode"
                                choices: [
                                    {
                                        name: "Original sound / EQ off",
                                        value: 0
                                    },
                                    {
                                        name: "Graphic EQ",
                                        value: 1
                                    },
                                    {
                                        name: "Speech / podcast",
                                        value: 2
                                    },
                                    {
                                        name: "Parametric EQ",
                                        value: 4
                                    }
                                ]
                            }
                            Setting {
                                title: "Bass boost"
                                settingKey: "bass_boost"
                            }
                        }
                        Section {
                            title: "Graphic equalizer"
                            subtitle: Rules.eqStatus(root.values.audio_mode, 1)
                            visible: !!root.hp.connected
                            HelpLabel {
                                title: "Graphic EQ and built-in presets"
                                topic: "graphic"
                            }
                            Action {
                                text: "Read graphic EQ"
                                onClicked: root.send({
                                    action: "graphic_read"
                                })
                            }
                            Loader {
                                id: graphicLoader
                                Layout.fillWidth: true
                                property bool reloading: false
                                active: !reloading && !!root.snapshot.graphic
                                sourceComponent: Component {
                                    ColumnLayout {
                                        id: graphicForm
                                        property var editors: []
                                        Layout.fillWidth: true
                                        spacing: 12
                                        Choice {
                                            model: ["Choose a preset…", "Neutral", "Rock", "Pop", "Dance", "Hip-Hop", "Classical", "Movie", "Jazz"]
                                            onActivated: {
                                                let presets = [[], [0, 0, 0, 0, 0], [0, 2, 2.5, 1.5, -2], [0, -2.5, 0, 2.5, 0], [3.5, 2, -1.5, 1.5, 3], [3, 1.5, -1.5, 0, -1.5], [-2, -1.5, 0, 3.5, 4], [0, 0, 2, 2, -2], [-3.2, 0, 2.2, 2.2, 0]];
                                                if (currentIndex > 0)
                                                    for (let i = 0; i < 5; ++i)
                                                        graphicForm.editors[i].text = String(presets[currentIndex][i]);
                                            }
                                        }
                                        Repeater {
                                            model: ["50 Hz", "250 Hz", "800 Hz", "3 kHz", "8 kHz"]
                                            RowLayout {
                                                required property int index
                                                required property string modelData
                                                Layout.fillWidth: true
                                                Copy {
                                                    text: modelData
                                                }
                                                Controls.TextField {
                                                    id: graphicGain
                                                    Layout.preferredWidth: 100
                                                    Component.onCompleted: {
                                                        text = String(root.snapshot.graphic[parent.index]);
                                                        graphicForm.editors[parent.index] = graphicGain;
                                                    }
                                                }
                                                Copy {
                                                    text: "dB"
                                                    Layout.fillWidth: false
                                                }
                                            }
                                        }
                                        Action {
                                            text: "Apply graphic EQ and enable it"
                                            onClicked: {
                                                let gains = [];
                                                for (let i = 0; i < 5; ++i)
                                                    gains.push(Number(graphicForm.editors[i].text));
                                                root.send({
                                                    action: "graphic_write",
                                                    gains: gains
                                                });
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        Section {
                            title: "Local EQ presets"
                            HelpLabel {
                                title: "Save and reuse your tuning"
                                topic: "presets"
                            }
                            Choice {
                                id: presetChoice
                                model: root.snapshot.presets || []
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                Action {
                                    text: "Load as draft"
                                    enabled: presetChoice.currentIndex >= 0 && !root.blockingBusy
                                    onClicked: root.send({
                                        action: "preset_load",
                                        name: presetChoice.currentText
                                    })
                                }
                                Action {
                                    text: "Delete preset"
                                    enabled: presetChoice.currentIndex >= 0 && !root.blockingBusy
                                    onClicked: root.send({
                                        action: "preset_delete",
                                        name: presetChoice.currentText
                                    })
                                }
                            }
                        }
                        Loader {
                            id: eqLoader
                            property bool reloading: false
                            Layout.fillWidth: true
                            active: !reloading && !!root.snapshot.peq
                            sourceComponent: eqForm
                        }
                    }
                    ColumnLayout {
                        visible: root.tab === "updates"
                        Layout.fillWidth: true
                        spacing: 20
                        Section {
                            title: "Firmware updates"
                            subtitle: "Check Sennheiser's official firmware catalog"
                            Copy {
                                text: "Checks run only when requested. This app checks versions; installation uses the official Sennheiser software."
                            }
                            Action {
                                text: "Check for firmware updates"
                                onClicked: root.send({
                                    action: "firmware_check"
                                })
                            }
                            Copy {
                                visible: !!root.snapshot.firmware_check
                                text: "Last checked: " + (root.snapshot.firmware_check ? root.snapshot.firmware_check.checked_at : "")
                                font.pixelSize: 12
                                opacity: .65
                            }
                        }
                        FirmwareStatus {
                            title: "BTD 700 dongle"
                            deviceKey: "dongle"
                            installed: root.dongle.firmware || ""
                            officialLabel: "Open Sennheiser Dongle Control download"
                            officialUrl: "https://eu.sennheiser-hearing.com/en-de/pages/sennheiser-dongle-control"
                        }
                        FirmwareStatus {
                            title: "HDB 630 headphones"
                            deviceKey: "headphones"
                            installed: root.values.firmware || ""
                            officialLabel: "Open Smart Control Plus information"
                            officialUrl: "https://us.sennheiser-hearing.com/products/hdb-630"
                        }
                    }
                }
            }
            ColumnLayout {
                id: panelFooter
                Layout.fillWidth: true
                spacing: 12
                Divider {}
                Action {
                    text: "Refresh status"
                    onClicked: root.send({
                        action: "refresh"
                    })
                }
            }
        }
    }
    Component {
        id: eqForm
        ColumnLayout {
            id: form
            property var bands: []
            spacing: 20
            Copy {
                text: "Parametric EQ · " + Rules.eqStatus(root.values.audio_mode, 4) + " Read EQ again to discard edits."
                opacity: .7
            }
            Section {
                title: "Save this draft locally"
                Controls.TextField {
                    id: presetName
                    Layout.fillWidth: true
                    placeholderText: "Preset name (existing names are replaced)"
                    maximumLength: 80
                }
                Action {
                    text: "Save local preset"
                    onClicked: {
                        let stages = [];
                        for (let i = 0; i < 5; ++i)
                            stages.push(form.bands[i].serialize());
                        root.send({
                            action: "preset_save",
                            name: presetName.text,
                            stages: stages,
                            pregain: Number(pre.text)
                        });
                    }
                }
            }
            Section {
                title: "Headroom"
                subtitle: "Leave space for any frequency boosts"
                HelpLabel {
                    title: "Pre-gain (−12 to 0 dB)"
                    topic: "pregain"
                }
                Controls.TextField {
                    id: pre
                    Layout.fillWidth: true
                    Component.onCompleted: text = String(root.snapshot.peq.pregain)
                }
            }
            Repeater {
                model: 5
                Section {
                    id: band
                    title: "Band " + (index + 1)
                    required property int index
                    Layout.fillWidth: true
                    Component.onCompleted: form.bands[index] = band
                    function serialize() {
                        return {
                            frequency: Number(freq.text),
                            gain: Number(gain.text),
                            q: Number(q.text),
                            filter: type.currentIndex
                        };
                    }
                    HelpLabel {
                        title: "Filter shape"
                        topic: "filter"
                        helpId: "filter-" + band.index
                    }
                    Choice {
                        id: type
                        Layout.fillWidth: true
                        model: ["Gain", "Low-pass 1", "High-pass 1", "All-pass 1", "Low shelf 1", "High shelf 1", "Tilt 1", "Low-pass 2", "High-pass 2", "All-pass 2", "High shelf", "Low shelf", "Tilt 2", "Bell", "Bypass"]
                        Component.onCompleted: currentIndex = root.snapshot.peq.stages[band.index].filter
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Repeater {
                            model: [
                                {
                                    name: "Hz",
                                    topic: "frequency"
                                },
                                {
                                    name: "dB",
                                    topic: "gain"
                                },
                                {
                                    name: "Q",
                                    topic: "q"
                                }
                            ]
                            RowLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.preferredWidth: 1
                                Copy {
                                    text: modelData.name
                                    font.pixelSize: 11
                                }
                                InfoButton {
                                    topic: modelData.topic
                                    helpId: "band" + band.index + ":" + modelData.topic
                                }
                            }
                        }
                    }
                    HelpCard {
                        visible: root.expandedHelp.indexOf("band" + band.index + ":") === 0
                        topic: visible ? root.expandedHelp.split(":")[1] : "eq"
                    }
                    Copy {
                        visible: type.currentIndex === 14
                        text: "This band is bypassed. Choose a filter to edit its parameters."
                        font.pixelSize: 12
                        opacity: .65
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Controls.TextField {
                            id: freq
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            placeholderText: "Hz"
                            Component.onCompleted: text = String(root.snapshot.peq.stages[band.index].frequency)
                        }
                        Controls.TextField {
                            id: gain
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            placeholderText: "dB"
                            Component.onCompleted: text = String(root.snapshot.peq.stages[band.index].gain)
                        }
                        Controls.TextField {
                            id: q
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            placeholderText: "Q"
                            Component.onCompleted: text = root.snapshot.peq.stages[band.index].q.toFixed(3)
                        }
                    }
                }
            }
            Copy {
                text: "Columns: frequency (Hz), gain (dB), Q. Shelf filters require Q from 0.25 to 0.71."
                opacity: .65
            }
            Section {
                title: "Apply equalizer"
                subtitle: "Save the edits, then choose whether EQ is active"
                Action {
                    text: root.values.audio_mode === 4 ? "Save EQ to headphones" : "Save parametric EQ (keep current mode)"
                    enabled: !!root.hp.connected && !root.blockingBusy
                    onClicked: {
                        let stages = [];
                        for (let i = 0; i < 5; ++i)
                            stages.push(form.bands[i].serialize());
                        root.send({
                            action: "peq_write",
                            stages: stages,
                            pregain: Number(pre.text)
                        });
                    }
                }
                Action {
                    text: root.values.audio_mode === 4 ? "Parametric EQ is active" : "Enable parametric EQ"
                    enabled: !!root.hp.connected && !root.blockingBusy && root.values.audio_mode !== 4
                    onClicked: root.change("audio_mode", 4)
                }
                Action {
                    text: root.values.audio_mode === 0 ? "EQ is already off" : root.values.audio_mode === 2 ? "Turn off speech processing" : "Disable EQ"
                    enabled: !!root.hp.connected && !root.blockingBusy && root.values.audio_mode !== 0
                    onClicked: root.change("audio_mode", 0)
                }
            }
        }
    }
}
