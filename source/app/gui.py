# GUI for FileSwoosh
# © 2024 Henri Wahl

from os import environ
from pathlib import Path
from sys import exit

from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QVariant
from PyQt6.QtWidgets import QApplication

from .config import ROOT_DIR
from .storage import hosts
from .helpers import file_url_prefix, get_all_addresses_filtered_as_text

# Set the style of the Qt Quick Controls to Basic to appear the same on all platforms
environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

class GUI(QApplication):
    """
    The GUI class extends QApplication to provide a graphical user interface for the application.
    It manages the application's main window and its interactions.

    Attributes:
        signal_confirm_transaction (pyqtSignal): Emitted to confirm a file transaction.
        signal_cancel_transaction (pyqtSignal): Emitted to cancel a file transaction.
        signal_hosts_updated (pyqtSignal): Emitted when the list of host addresses changes.
        signal_request_transaction (pyqtSignal): Emitted to request a file transaction.
        signal_transaction_requested (pyqtSignal): Emitted when a file transaction is requested.
        signal_add_host_manually (pyqtSignal): Emitted to add a host address manually.
    """
    signal_confirm_transaction = pyqtSignal(str, str)
    signal_cancel_transaction = pyqtSignal(str)
    signal_hosts_updated = pyqtSignal(QVariant)
    signal_request_transaction = pyqtSignal(str, str)
    signal_transaction_requested = pyqtSignal(str, str, str, str, str, str)
    signal_add_host_manually = pyqtSignal(str, str)

    def __init__(self, argv=list()):
        """
        Initializes the GUI application.

        This method sets up the QML application engine, loads the main QML file, and exposes necessary
        properties and the GUI instance itself to the QML context for interaction.

        Args:
            argv (list): A list of arguments passed to the application. Defaults to an empty list.
        """
        super().__init__(argv)  # Initialize the QApplication base class with any command line arguments.
        self.engine = QQmlApplicationEngine()  # Create a new QQmlApplicationEngine instance.
        # Set the 'addresses' property in the QML context to the result of get_all_addresses_as_text().
        self.engine.rootContext().setContextProperty('addresses', get_all_addresses_filtered_as_text())
        # Expose the GUI instance to the QML context, allowing QML to interact with the GUI.
        self.engine.rootContext().setContextProperty('gui', self)
        # Expose the file URL prefix to the QML context, used for file operations in QML.
        self.engine.rootContext().setContextProperty('file_url_prefix', file_url_prefix)
        # Load the main QML file from the resources directory.
        self.engine.load(str(ROOT_DIR / 'resources' / 'qml' / 'main.qml'))

        # If no root QML objects are loaded, exit the application with an error code.
        if not self.engine.rootObjects():
            exit(-1)

    @pyqtSlot(str, str)
    def slot_request_transaction(self, address: str, file_path: str):
        """
        Slot to handle the request for initiating a file transaction.

        This method emits a signal to request a file transaction, providing the address of the recipient
        and the path of the file to be sent. It is connected to the signal_request_transaction signal,
        which should be connected to the appropriate handler to process the transaction request.

        Args:
            address (str): The network address of the recipient.
            file_path (str): The path of the file to be sent.
        """
        self.signal_request_transaction.emit(address, file_path)

    @pyqtSlot(str, str, str, str, str, str)
    def slot_transaction_requested(self, address: str, hostname: str, username: str, file_name: str, transaction_id: str, save_folder_qml: str):
        """
        Slot to emit a signal for a requested file transaction with all necessary details.

        This method is triggered when a file transaction is requested. It emits a signal with the
        details of the transaction, including the address, hostname, username, file name, transaction ID,
        and the save folder path.

        Args:
            address (str): The network address of the host requesting the transaction.
            hostname (str): The hostname of the requesting host.
            username (str): The username of the user on the requesting host.
            file_name (str): The name of the file to be transacted.
            transaction_id (str): A unique identifier for the transaction.
            save_folder_qml (str): The path to the folder where the file should be saved.
        """
        self.signal_transaction_requested.emit(address, hostname, username, file_name, transaction_id, save_folder_qml)

    @pyqtSlot()
    def slot_hosts_updated(self):
        """
        Slot to handle the event when the list of host addresses changes.

        This method is triggered whenever there is a change in the list of host addresses. It emits a
        signal with a dictionary where each key-value pair represents an address and its corresponding
        host details. The host details are obtained by calling the `get_as_dict` method on each host
        object.
        """
        self.signal_hosts_updated.emit({address: host.get_as_dict() for address, host in hosts.items()})

    @pyqtSlot(str, str)
    def slot_confirm_transaction(self, transaction_id: str, save_folder: str):
        """
        Slot to confirm a file transaction.

        This method is invoked to confirm a file transaction, emitting a signal with the transaction ID
        and the save folder path.

        Args:
            transaction_id (str): The unique identifier for the transaction.
            save_folder (str): The path to the folder where the file should be saved.
        """
        self.signal_confirm_transaction.emit(transaction_id, save_folder)

    @pyqtSlot(str)
    def slot_cancel_transaction(self, transaction_id: str):
        """
        Slot to cancel a file transaction.

        This method is invoked to cancel a file transaction, emitting a signal with the transaction ID.
        Happens when a user does not confirm the transaction.

        Args:
            transaction_id (str): The unique identifier for the transaction to be cancelled.
        """
        self.signal_cancel_transaction.emit(transaction_id)

    @pyqtSlot(str, str)
    def slot_add_host_manually(self, hostname: str, address: str):
        """
        Slot to manually add a host.

        This method is invoked to add a new host manually by emitting a signal with the hostname and network address.
        It is connected to the signal_add_host_manually signal, which is emitted to add the host to the application's
        known hosts list.

        Args:
            hostname (str): The hostname of the new host to be added.
            address (str): The network address of the new host to be added.
        """
        self.signal_add_host_manually.emit(hostname, address)