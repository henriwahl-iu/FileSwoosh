# Discovery and host management for FileSwoosh
# © 2024 Henri Wahl

from datetime import datetime, timedelta
from ipaddress import ip_address
from socket import AF_INET6
from time import sleep

from multicast_expert import McastTxSocket
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot

from ..config import MULTICAST_ADDRESS, PORT, TIME_TO_LIVE
from ..helpers import get_default_address
from ..storage import Host, hosts, transactions

class DiscoveryThread(QThread):
    """
    A thread dedicated to discovering hosts on the network via multicast.

    This thread continuously sends multicast messages to discover other hosts
    and updates the global hosts dictionary with any new or removed hosts based
    on their response and timestamp.

    Attributes:
        signal_hosts_updated (pyqtSignal): Signal to emit when the list of hosts changes.
    """

    signal_hosts_updated = pyqtSignal()

    def run(self):
        """
        The main loop of the discovery thread.

        Sends multicast messages to a predefined address and port, checks for hosts
        that have not responded within a certain timeframe, and updates the global
        hosts dictionary accordingly.
        """
        default_address = get_default_address()

        with McastTxSocket(addr_family=AF_INET6, mcast_ips=[MULTICAST_ADDRESS],
                           iface_ip=default_address) as tx_socket:
            while True:
                # Send a multicast message to discover hosts
                tx_socket.sendto(f'is there anybody out there?'.encode('UTF-8'), (MULTICAST_ADDRESS, PORT))
                # Update the known hosts
                self.update_hosts()
                # Emit a signal to indicate that the list of hosts has been updated
                self.signal_hosts_updated.emit()
                # Wait for the next transmission of the multicast signal
                sleep(0.25)

    def update_hosts(self):
        now = datetime.now()
        # Remove hosts that have not responded within the TIME_TO_LIVE + some tolerance period
        for address in {address: host for address, host in hosts.items() if
                        now - host.timestamp > timedelta(seconds=TIME_TO_LIVE) and
                        host.discovered}.keys():
            del hosts[address]
            # Cancel transactions for removed hosts
            for transaction_id in transactions['in']:
                if transactions['in'][transaction_id].address == address:
                    transactions['in'][transaction_id].stage = 'canceled'

    @pyqtSlot(str, str)
    def add_host_manually(self, hostname: str = '', address: str = ''):
        """
        Adds a host manually to the global hosts dictionary.

        This method allows for manual addition of hosts by specifying a hostname
        and address. It also emits a signal to indicate that the list of hosts has changed.

        Args:
            hostname (str): The hostname of the host to add.
            address (str): The IP address of the host to add.
        """
        try:
            address = address.strip()
            if not hosts.get(address):
                hosts[address] = Host(address=address,
                                      hostname=hostname,
                                      discovered=False)
                # Emit a signal to indicate that the list of hosts has changed
                self.signal_hosts_updated.emit()
        except ValueError:
            print(f'Invalid address: "{address}"')