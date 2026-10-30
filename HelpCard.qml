pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import qs.Commons
import qs.Commons as Commons
import "HelpData.js" as Help

Rectangle {
    id: card
    property string topic: ""
    property real level: 0
    readonly property var info: Help.get(topic)
    readonly property color ink: Commons.Color.foreground
    readonly property color accent: Commons.Color.accent
    readonly property string textFont: Style.font.family
    Layout.fillWidth: true
    implicitHeight: content.implicitHeight + 24
    radius: 6
    color: Qt.alpha(ink, 0.045)
    border.color: Qt.alpha(ink, 0.1)
    border.width: 1

    ColumnLayout {
        id: content
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 12
        spacing: 10
        Text {
            Layout.fillWidth: true
            text: card.info.title
            textFormat: Text.PlainText
            wrapMode: Text.WordWrap
            color: card.ink
            font.family: card.textFont
            font.pixelSize: 13
            font.bold: true
        }
        Canvas {
            id: illustration
            Layout.fillWidth: true
            Layout.preferredHeight: 95
            visible: !!card.info.visual
            onWidthChanged: requestPaint()
            Connections {
                target: card
                function onLevelChanged() { illustration.requestPaint() }
                function onInfoChanged() { illustration.requestPaint() }
                function onInkChanged() { illustration.requestPaint() }
                function onAccentChanged() { illustration.requestPaint() }
            }
            onPaint: {
                let c = getContext("2d"), w = width, h = height
                c.clearRect(0, 0, w, h)
                c.font = "11px sans-serif"
                c.lineWidth = 2
                function text(label, x, y, align) {
                    c.fillStyle = card.ink; c.textAlign = align || "left"; c.fillText(label, x, y)
                }
                function line(x1, y1, x2, y2, opacity) {
                    c.strokeStyle = Qt.alpha(card.accent, opacity === undefined ? 1 : opacity)
                    c.beginPath(); c.moveTo(x1, y1); c.lineTo(x2, y2); c.stroke()
                }
                if (card.info.visual === "transparency") {
                    text("MORE CANCELLATION", 0, 12)
                    text("MORE OUTSIDE SOUND", w, 12, "right")
                    let p = Math.max(0, Math.min(1, card.level / 100))
                    c.fillStyle = Qt.alpha(card.ink, .12); c.fillRect(3, 38, w-6, 6)
                    c.fillStyle = card.accent; c.fillRect(3, 38, (w-6)*p, 6)
                    c.beginPath(); c.arc(3+(w-6)*p, 41, 6, 0, 2*Math.PI); c.fill()
                    text("0%", 0, 68); text(Math.round(card.level)+"%", w/2, 68, "center"); text("100%", w, 68, "right")
                    text("Manual balance · music volume stays the same", w/2, 90, "center")
                } else if (card.info.visual === "crossfeed") {
                    let p = card.level === 2 ? 0 : (card.level === 1 ? .8 : .35)
                    text("Left channel", 0, 12); text("Right channel", w, 12, "right")
                    line(28, 24, 28, 65); line(w-28, 24, w-28, 65)
                    line(35, 24, w-35, 65, p); line(w-35, 24, 35, 65, p)
                    text("Left ear", 0, 90); text(p ? (card.level === 1 ? "High blend" : "Low blend") : "No blend", w/2, 90, "center"); text("Right ear", w, 90, "right")
                } else {
                    line(0, 60, w, 60, .25)
                    for (let narrow = 0; narrow <= 1; narrow++) {
                        c.strokeStyle = Qt.alpha(card.accent, narrow ? 1 : .4)
                        c.beginPath()
                        for (let x=0; x<=w; x++) {
                            let sigma = w*(narrow ? .055 : .18)
                            let y = 60-40*Math.exp(-.5*Math.pow((x-w*.5)/sigma, 2))
                            if (x===0) c.moveTo(x,y); else c.lineTo(x,y)
                        }
                        c.stroke()
                    }
                    text("Bass", 0, 90); text("Mids", w/2, 90, "center"); text("Treble", w, 90, "right")
                    text("Bell filter: broad vs narrow Q", w/2, 12, "center")
                }
            }
        }
        Text {
            Layout.fillWidth: true
            text: card.info.body
            textFormat: Text.PlainText
            wrapMode: Text.WordWrap
            color: card.ink
            font.family: card.textFont
            font.pixelSize: 13
            lineHeight: 1.2
        }
    }
}
