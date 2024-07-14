/*
 * Custom button component with rounded corners
 */

import QtQuick
import QtQuick.Controls

Button {

    property string color: "blue"
    property string textColor: "white"

    padding: 10
    background: Rectangle {
        color: pressed ? "dark" + parent.color : parent.color
        radius: 5
    }
    contentItem: Label {
        text: parent.text
        color: textColor
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

}