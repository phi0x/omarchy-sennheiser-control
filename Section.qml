pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import qs.Commons
import qs.Commons as Commons

Rectangle {
    id: section
    readonly property color ink: Commons.Color.foreground
    readonly property string fontName: Style.font.family
    property string title: ""
    property string subtitle: ""
    default property alias content: body.data
    Layout.fillWidth: true
    implicitHeight: stack.implicitHeight + 32
    radius: 8
    color: Qt.alpha(section.ink, .025)
    border.width: 1
    border.color: Qt.alpha(section.ink, .14)
    ColumnLayout {
        id: stack
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 16
        spacing: 16
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 5
            visible: section.title !== ""
            Text {
                Layout.fillWidth: true
                text: section.title
                textFormat: Text.PlainText
                wrapMode: Text.WordWrap
                color: section.ink
                font.family: section.fontName
                font.pixelSize: 15
                font.bold: true
            }
            Text {
                Layout.fillWidth: true
                visible: section.subtitle !== ""
                text: section.subtitle
                textFormat: Text.PlainText
                wrapMode: Text.WordWrap
                color: Qt.alpha(section.ink, .6)
                font.family: section.fontName
                font.pixelSize: 12
            }
        }
        ColumnLayout {
            id: body
            Layout.fillWidth: true
            spacing: 14
        }
    }
}
