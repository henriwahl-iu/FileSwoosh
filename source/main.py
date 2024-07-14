#!/usr/bin/env python3
#
# FileSwoosh - A simple file transfer tool
# © 2024 Henri Wahl
#
from sys import argv

from PyQt6.QtGui import QIcon

from app.backend.discovery import DiscoveryThread
from app.backend.client import ClientThread
from app.backend.server import ServerThread
from app.config import ROOT_DIR, PLATFORM
from app.gui import GUI


if __name__ == "__main__":
    # On Windows Flask can't run IPv4 and IPv6 on one socket
    if PLATFORM == 'Windows':
        server_thread_ipv4 = ServerThread('0.0.0.0')
        server_thread_ipv4.start()

    server_thread_ipv6 = ServerThread('::')
    server_thread_ipv6.start()

    client_thread = ClientThread()
    client_thread.start()

    discovery_thread = DiscoveryThread()
    discovery_thread.start()
    gui = GUI(argv=argv)
    gui.setWindowIcon(QIcon(str(ROOT_DIR / 'resources' / 'images' / 'logo.svg')))

    discovery_thread.signal_hosts_updated.connect(gui.slot_hosts_updated)

    if PLATFORM == 'Windows':
        server_thread_ipv4.signal_transaction_requested.connect(gui.slot_transaction_requested)
        server_thread_ipv4.signal_start_transaction.connect(client_thread.start_transaction)

    server_thread_ipv6.signal_transaction_requested.connect(gui.slot_transaction_requested)
    server_thread_ipv6.signal_start_transaction.connect(client_thread.start_transaction)

    gui.signal_request_transaction.connect(client_thread.request_transaction)
    gui.signal_confirm_transaction.connect(client_thread.confirm_transaction)
    gui.signal_cancel_transaction.connect(client_thread.cancel_transaction)
    gui.signal_add_host_manually.connect(discovery_thread.add_host_manually)

    gui.exec()