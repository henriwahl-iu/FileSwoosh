# Storage and models for FileSwoosh
# © 2024 Henri Wahl

import copy
from datetime import datetime
from pathlib import Path

from .helpers import save_folder

# Global dictionaries to store hosts and transactions information
hosts = {}
transactions = {'in': dict(),
                'out': dict()}
# Cache for link-local addresses to connect link local addresses
# with their appropriate scope IDs
link_local_address_cache = dict()


class Transaction:
    """
    Represents a file transaction between hosts.

    Attributes:
        address (str): Network address of the other party in the transaction.
        file_path (Path): Local path to the file being transferred.
        transaction_id (str): Unique identifier for the transaction.
        stage (str): Current stage of the transaction (e.g., 'requested', 'confirmed').
        save_folder (Path): Destination folder for saving the file.
    """

    def __init__(self, address: str = None,
                 file_path: Path = None,
                 transaction_id: str = None,
                 stage: str = 'requested', ):
        self.address = address
        self.file_path = file_path
        self.transaction_id = transaction_id
        self.stage = stage
        self.save_folder = copy.copy(save_folder)


class Host:
    """
    Represents a network host with which file transactions can occur.

    Attributes:
        address (str): Network address of the host.
        hostname (str): Hostname of the host.
        username (str): Username of the user on the host.
        timestamp (datetime): Timestamp of when the host was discovered or updated.
        discovered (bool): Flag indicating whether the host was discovered in the network.
        busy (bool): Property indicating whether the host is currently involved in a transaction.
    """

    def __init__(self,
                 address: str = '',
                 hostname: str = '',
                 username: str = '',
                 discovered: bool = True):
        self.address = address
        self.hostname = hostname
        self.username = username
        self.timestamp = datetime.now()
        self.discovered = discovered

    @property
    def busy(self):
        """
        Checks if the host is currently involved in any 'confirmed' or 'requested' transactions.

        Returns:
            bool: True if the host is busy, False otherwise.
        """
        for transaction_id in transactions['out']:
            if transactions['out'].get(transaction_id):
                if transactions['out'][transaction_id].address == self.address and \
                        transactions['out'][transaction_id].stage in ['confirmed', 'requested']:
                    return True
        for transaction_id in transactions['in']:
            if transactions['in'].get(transaction_id):
                if transactions['in'][transaction_id].address == self.address and \
                        transactions['in'][transaction_id].stage in ['confirmed', 'requested']:
                    return True
        return False

    def get_as_dict(self) -> dict:
        """
        Converts the host's attributes to a dictionary to be used in QML.

        Returns:
            dict: A dictionary representation of the host's attributes.
        """
        return {'address': self.address,
                'hostname': self.hostname,
                'username': self.username,
                'timestamp': self.timestamp,
                'discovered': self.discovered,
                'busy': self.busy}
