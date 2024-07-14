/*
 * Custom button component with rounded corners
 */

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

// import components, containing MyButton
import "components"

// Main window of the application
ApplicationWindow {
    property int minWidth: 410 // Minimum width of the application window
    id: appWindow
    visible: true // Makes the window visible upon application start
    width: minWidth // Initial width of the window
    height: 480 // Initial height of the window
    minimumWidth: minWidth // Sets the minimum width to prevent resizing below this width
    title: "FileSwoosh"

    header: ToolBar {
        contentHeight: menuButton.height // Sets the toolbar height to match the menu button's height
        RowLayout {
            anchors.fill: parent // Ensures the layout fills the toolbar

            Item {
                id: spacerMenu
                Layout.fillWidth: true // Spacer to push the menu button to the right
            }
            ToolButton {
                id: menuButton
                icon.source: "../images/menu.svg"
                onClicked: menu.open() // Opens the menu when the button is clicked
            }
        }

        Menu {
            id: menu
            x: appWindow.width - width // Positions the menu on the right side of the window
            y: height - menuButton.height // Aligns the menu vertically with the toolbar
            width: 220
            MenuItem {
                text: "Add remote host address" // Menu item for adding a remote host address
                icon.source: "../images/plus.svg"
                onTriggered: {
                    addHostDialog.open() // Opens the dialog to add a host address
                }
            }
            MenuItem {
                text: "Show my host addresses" // Menu item to show host addresses
                icon.source: "../images/info-circle.svg"
                onTriggered: {
                    addressesDialog.open() // Opens the dialog displaying host addresses
                }
            }
        }
    }

    //
    ColumnLayout {
        anchors.fill: parent // Fills the parent container to use all available space
        anchors.topMargin: 5 // Adds a margin to the top of the layout
        GridView {
            id: hostsGridView
            Layout.fillWidth: true // GridView fills the width of its parent
            Layout.fillHeight: true // GridView fills the height of its parent
            model: hostsModel // Data model for the GridView items
            cellHeight: 80 // Height of each cell in the GridView
            boundsBehavior: Flickable.StopAtBounds // Prevents scrolling beyond the content bounds

            // Calculates the number of items per row based on the window width and minimum width
            property int itemsPerRow: Math.max(1, Math.floor(appWindow.width / minWidth))

            // Calculates the cell width dynamically to accommodate varying screen sizes and orientations
            cellWidth: Math.max(minWidth, Math.max(appWindow.width / itemsPerRow, minWidth))

            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded // Displays the vertical scrollbar as needed
            }

            delegate: Item {
                width: hostsGridView.cellWidth // Sets the delegate item width to the calculated cell width
                height: 80 // Sets the delegate item height

                MouseArea {
                    id: mouseArea
                    anchors.fill: parent // MouseArea fills the entire delegate item
                    cursorShape: Qt.PointingHandCursor // Changes the cursor to a pointing hand
                    hoverEnabled: true // Enables hover state detection
                    onClicked: {
                        // Opens the file dialog if the model item is not busy
                        if (!model.busy) {
                            openFileDialog.model = model
                            openFileDialog.open()
                        }
                    }
                }

                Rectangle {
                    id: background
                    anchors.fill: parent // Background fills the entire delegate item
                    // Changes the background color based on hover state
                    color: (hostLabelMouseArea.containsMouse || mouseArea.containsMouse) ? "lightgreen" : "lightblue"
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    anchors.topMargin: 5
                    anchors.bottomMargin: 5
                    radius: 15 // Sets the corner radius for rounded corners

                    Image {
                        id: hostIcon
                        source: "../images/laptop.svg" // Source path of the icon image
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        height: background.height - 10
                        width: background.height - 10
                        anchors.leftMargin: 10
                        visible: !model.busy // Only visible if the model item is not busy
                    }
                    BusyIndicator {
                        id: busyIndicator
                        width: background.height - 10
                        height: background.height - 10
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.leftMargin: 10
                        running: model.busy // Indicates whether the model item is busy
                        visible: model.busy // Only visible if the model item is busy
                    }
                    Text {
                        anchors.left: hostIcon.right
                        anchors.verticalCenter: hostIcon.verticalCenter
                        anchors.leftMargin: 10
                        width: hostsGridView.cellWidth - hostIcon.width - 20
                        id: hostLabel
                        // Displays the username and hostname in bold, and the address in a smaller font
                        text: '<b>' + model.username + ' @ ' + model.hostname +
                            '</b><br><small><font color="#444444">' + model.address + '</font></small>'

                        MouseArea {
                            id: hostLabelMouseArea
                            anchors.fill: parent // Ensures the MouseArea fills the entire parent item.
                            cursorShape: Qt.PointingHandCursor // Changes the cursor to a pointing hand when hovered over.
                            hoverEnabled: true // Enables detection of hover events.
                            onClicked: {
                                openFileDialog.model = model // Sets the model of the openFileDialog to the current model.
                                openFileDialog.open() // Opens the file dialog.
                            }
                        }
                    }
                }
            }
        }
    }

    // Dialog for confirming incoming file transactions
    Dialog {
        id: requestTransactionDialog
        title: "Confirm incoming file"
        modal: true
        width: appWindow.width

        // Properties to hold transaction details
        property string address: ""
        property string hostname: ""
        property string username: ""
        property string file_name: ""
        property string transaction_id: ""
        property string save_folder: saveFolderDialog.currentFolder

        closePolicy: Dialog.CloseOnEscape

        ColumnLayout {
            anchors.fill: parent
            spacing: 10

            // Displays transaction details to the user
            Text {
                text:
                    '<b>' + requestTransactionDialog.username + ' @ ' + requestTransactionDialog.hostname + '</b><br>' +
                    'from host <b>' + requestTransactionDialog.address + '</b><br>' +
                    'wants to send you the file<br><br>' +
                    '<b>' + requestTransactionDialog.file_name + '</b><br><br>' +
                    'which will be saved at:<br><br>' +
                    '<b>' + requestTransactionDialog.save_folder.split(file_url_prefix)[1] + '</b><br><br>'
                Layout.alignment: Qt.AlignCenter
            }

            // Row layout for action buttons
            RowLayout {
                Layout.alignment: Qt.AlignCenter
                // Button to cancel the transaction
                MyButton {
                    id: buttonCancel
                    text: "Cancel"
                    color: "red"
                    onClicked: {
                        requestTransactionDialog.close()
                        // Sends a signal to the GUI object to cancel the transaction
                        gui.slot_cancel_transaction(requestTransactionDialog.transaction_id)
                    }
                }
                // Button to open dialog for selecting a save folder
                MyButton {
                    id: buttonSaveAt
                    text: "Choose folder to save..."
                    color: "blue"
                    onClicked: {
                        saveFolderDialog.open()
                    }
                }

                // Button to confirm the transaction and save the file
                MyButton {
                    id: buttonSave
                    text: "Save"
                    color: "green"
                    onClicked: {
                        requestTransactionDialog.close()
                        gui.slot_confirm_transaction(requestTransactionDialog.transaction_id, saveFolderDialog.currentFolder)
                    }
                }
            }
        }
    }

    // File dialog for selecting a file to send
    FileDialog {
        id: openFileDialog
        title: "Please choose a file"
        // Property to hold the model associated with the dialog. This model contains data needed for the transaction.
        property var model: null

        onAccepted: {
            // Slot to handle the 'accepted' signal. When a file is selected and the dialog is accepted,
            // this slot requests a transaction with the selected file's path and the model's address.
            gui.slot_request_transaction(model.address, openFileDialog.selectedFile)
        }
    }

    // Dialog for selecting a folder to save the incoming file
    FolderDialog {
        id: saveFolderDialog
        title: "Please choose a folder to save at..."
    }

    // Data model for the GridView items
    ListModel {
        id: hostsModel
    }

    // Signal connections to the GUI object
    Connections {
        target: gui // GUI thread in main application

        // Handles changes in the list of host addresses.
        // This function updates the hostsModel with new or updated host entries.
        function onSignal_hosts_updated(newHosts) {
            // Iterate over the newHosts object to update or add hosts.
            for (var host in newHosts) {

                var found = false;
                // Check if the host already exists in the model.
                for (var i = 0; i < hostsModel.count; i++) {
                    if (hostsModel.get(i).address === newHosts[host].address) {
                        found = true;
                        break;
                    }
                }
                // If the host is not found, append it to the model.
                if (!found) {
                    hostsModel.append({
                        "hostname": newHosts[host].hostname,
                        "username": newHosts[host].username,
                        "address": newHosts[host].address,
                        "busy": newHosts[host].busy
                    });
                }
            }

            // Remove hosts that are no longer present in newHosts.
            for (var i = hostsModel.count - 1; i >= 0; i--) {
                var found = false;
                for (var host in newHosts) {
                    if (hostsModel.get(i).address === newHosts[host].address) {
                        // Update the 'busy' status of existing hosts.
                        hostsModel.get(i).busy = newHosts[host].busy;
                        found = true;
                        break;
                    }
                }
                // If the host is not found in newHosts, remove it from the model.
                if (!found) {
                    hostsModel.remove(i);
                }
            }
        }

        // Handles a request for a file transaction.
        // This function sets up the requestTransactionDialog with the transaction details.
        function onSignal_transaction_requested(address, hostname, username, file_name, transaction_id, save_folder_qml) {
            requestTransactionDialog.address = address; // The address of the host initiating the transaction.
            requestTransactionDialog.hostname = hostname; // The hostname of the initiating host.
            requestTransactionDialog.username = username; // The username of the initiating user.
            requestTransactionDialog.file_name = file_name; // The name of the file being sent.
            requestTransactionDialog.transaction_id = transaction_id; // A unique identifier for the transaction.
            saveFolderDialog.currentFolder = save_folder_qml; // The default folder to save the incoming file.
            requestTransactionDialog.open(); // Opens the dialog to confirm the transaction.
        }
    }
    // Dialog for displaying host addresses
    Dialog {
        id: addressesDialog
        title: "My host addresses"
        modal: true
        width: appWindow.width // Sets the dialog width to match the application window width.
        closePolicy: Dialog.CloseOnEscape // Allows the dialog to be closed using the Escape key.
        ColumnLayout {
            anchors.fill: parent // Ensures the layout fills the dialog.
            spacing: 10

            TextArea {
                readOnly: true // Disables editing of the text area.
                text: addresses
                Layout.alignment: Qt.AlignCenter // Centers the text area within its layout.
            }

            MyButton {
                text: "OK"
                Layout.alignment: Qt.AlignRight
                color: "green"
                onClicked: {
                    addressesDialog.close()
                }
            }
        }
    }

    // Dialog for adding a remote host address
    Dialog {
        id: addHostDialog
        title: "Add remote host address"
        modal: true
        width: appWindow.width
        onOpened: {
            //
            hostNameField.text = "";
            ipAddressField.text = "";
            hostNameField.focus = true // Set focus on the TextField when the dialog opens
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 10

            TextField {
                id: hostNameField
                placeholderText: "Hostname" // Placeholder text for the host name field
                Layout.fillWidth: true
            }

            TextField {
                id: ipAddressField
                placeholderText: "IP Address" // Placeholder text for the IP address field
                Layout.fillWidth: true
                // Validates the IP address input using regular expressions
                onTextChanged: {
                    var ipv4Pattern = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
                    var ipv6Pattern = /^(?:(?:[A-Fa-f0-9]{1,4}:){7}(?:[A-Fa-f0-9]{1,4}|:))$|^(?:(?:[A-Fa-f0-9]{1,4}:){6}(?:[A-Fa-f0-9]{1,4}|:)(?:[A-Fa-f0-9]{1,4}|:))$|^(?:(?:[A-Fa-f0-9]{1,4}:){5}(?::[A-Fa-f0-9]{1,4}){1,2})$|^(?:(?:[A-Fa-f0-9]{1,4}:){4}(?::[A-Fa-f0-9]{1,4}){1,3})$|^(?:(?:[A-Fa-f0-9]{1,4}:){3}(?::[A-Fa-f0-9]{1,4}){1,4})$|^(?:(?:[A-Fa-f0-9]{1,4}:){2}(?::[A-Fa-f0-9]{1,4}){1,5})$|^(?:(?:[A-Fa-f0-9]{1,4}:){1}(?::[A-Fa-f0-9]{1,4}){1,6})$|^:(?::[A-Fa-f0-9]{1,4}){1,7}$/;
                    if (ipv4Pattern.test(ipAddressField.text) || ipv6Pattern.test(ipAddressField.text)) {
                        // Input is valid
                        ipAddressField.color = "black";
                    } else {
                        // Input is invalid
                        ipAddressField.color = "red";
                    }
                }
            }

            RowLayout {
                Layout.alignment: Qt.AlignRight
                Layout.fillWidth: true

                MyButton {
                    text: "Cancel"
                    color: "red"
                    onClicked: addHostDialog.close()
                }

                MyButton {
                    id: addHostButton
                    // Enables the button if the input fields are not empty and the IP address is valid
                    enabled: hostNameField.text.length > 0 && ipAddressField.color !== "red" && ipAddressField.text.length > 0
                    // Disables the button if the input fields are empty or the IP address is invalid
                    opacity: enabled ? 1 : 0.5
                    text: "Add"
                    color: "green"
                    //
                    onClicked: {
                        gui.slot_add_host(hostNameField.text, ipAddressField.text)
                        addHostDialog.close()
                    }
                }
            }
        }
    }
}