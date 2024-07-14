# Server part of FileSwoosh
# © 2024 Henri Wahl

import logging
from ipaddress import ip_address
from json import loads
from uuid import uuid4

from PyQt6.QtCore import QThread, pyqtSignal
from flask import Flask, request, jsonify

from app.config import PORT
from app.helpers import qmlify_file_path, save_folder, generate_unique_file_name, get_all_addresses
from app.storage import hosts, Host, transactions, Transaction

# Suppress the warnings from Flask's default logger to clean up the console output.
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Create two Flask app instances for handling IPv4 and IPv6 requests separately.
http_server_ipv4 = Flask(f'{__name__}_ipv4')
http_server_ipv6 = Flask(f'{__name__}_ipv6')

class ServerThread(QThread):
    """
    A QThread subclass that encapsulates a Flask server to handle HTTP requests.

    This server is designed to operate in a separate thread from the main GUI thread,
    allowing for asynchronous handling of network requests without blocking the UI.

    Attributes:
        signal_transaction_requested (pyqtSignal): Emitted when a transaction request is received.
        signal_start_transaction (pyqtSignal): Emitted to start a file transaction.
    """

    # Signals to communicate with the main GUI thread.
    signal_transaction_requested = pyqtSignal(str, str, str, str, str, str)
    signal_start_transaction = pyqtSignal(str)

    def __init__(self, listen_address: str = ''):
        """
        Initializes the server thread with a specific listening address.

        Args:
            listen_address (str): The IP address on which the server will listen for incoming connections.
        """
        super().__init__()

        # Define the HTTP methods allowed by the server.
        METHODS = ['POST']

        self.listen_address = listen_address

        # Determine whether to use the IPv4 or IPv6 Flask app based on the listen address.
        if ip_address(self.listen_address).version == 6:
            self.http_server = http_server_ipv6
        else:
            self.http_server = http_server_ipv4

        # Register URL rules for handling different types of requests.
        self.http_server.add_url_rule('/connect', 'connect', self.connect, methods=METHODS)
        # Register URL rules for handling transaction-related requests and a catchall for undefined routes.
        # Endpoint to confirm a transaction request.
        self.http_server.add_url_rule('/confirm-transaction', 'confirm-transaction', self.confirm_transaction,
                                      methods=METHODS)
        # Endpoint to cancel a transaction request.
        self.http_server.add_url_rule('/cancel-transaction', 'cancel-transaction', self.cancel_transaction,
                                      methods=METHODS)
        # Endpoint for a new transaction request.
        self.http_server.add_url_rule('/request-transaction', 'request-transaction', self.request_transaction,
                                      methods=METHODS)
        # Endpoint to start a transaction after receiving the confirmation.
        self.http_server.add_url_rule('/start-transaction', 'start-transaction', self.start_transaction,
                                      methods=METHODS)
        # Catchall routes to handle undefined or incorrect paths.
        self.http_server.add_url_rule('/<path:path>', 'catch_all', self.catch_all, methods=METHODS)  # Catchall for any undefined path.
        self.http_server.add_url_rule('/', 'catch_all', self.catch_all, methods=METHODS)  # Root path catchall.

    def run(self):
        # Starts the Flask server with the specified host, port, and SSL context.
        # SSL context is 'adhoc' because of easier certificate management and
        # honestly being simply adhoc.
        self.http_server.run(host=self.listen_address,
                             port=PORT,
                             threaded=True,
                             ssl_context='adhoc')

    def catch_all(self, path: str = ''):
        """
        A catch-all route handler that returns a simple message indicating the path is unknown.

        Args:
            path (str): The path that was requested and did not match any defined route.

        Returns:
            str: A message indicating that the requested path is unknown.
        """

        return f'{path} unknown'

    def connect(self):
        """
        Handles connection requests from clients, registering the client's host information.

        After receiving the discovery packet via multicast, the remote host sends the request
        to the 'connect' endpoint to get known to this host. The remote host will be stored in
        the global hosts dictionary with its remote address as the key.
        The response is of no use for the client as it just intended to publish itself.

        Returns:
            flask.Response: A JSON response containing information about the host, suitable
                            for informing the client about the current state or configuration
                            of the host within the application.
        """

        data = request.get_json()

        # Store the host information in the global hosts dictionary.
        if request.remote_addr not in get_all_addresses():
            hosts[request.remote_addr] = Host(address=request.remote_addr,
                                              hostname=data.get('hostname'),
                                              username=data.get('username'))
        # Return a simple JSON response to indicate the connection was successful.
        return jsonify({'status': 'ok'})

    def request_transaction(self):
        """
        Handles a request to initiate a new file transaction.

        This method processes a transaction request received from a client. It extracts the client's
        information from the JSON payload and checks if the client's address is already known. If known,
        it generates a unique transaction ID, creates a new transaction entry in the global transactions
        dictionary, and emits a signal to notify the main GUI thread. The method returns a JSON response
        with the transaction ID if successful, or an error status if the client's address is not recognized.

        Args:
            self: Access to class attributes and methods.

        Returns:
            flask.Response: A JSON response containing the transaction ID if the request is successful,
                            or an error status if the client's address is not recognized.
        """
        data = request.get_json()
        # Linux hosts trying to connect to a Windows host via IPv4 will use
        # the IPv6 stack with an IPv4-mapped address. This check removes the
        if request.remote_addr.startswith('::ffff:'):
            remote_address = request.remote_addr.split('::ffff:')[1]
        else:
            remote_address = request.remote_addr
        # Check if the client's address is known and create a new transaction if so.
        if hosts.get(remote_address):
            # Generate a unique transaction ID and create a new transaction entry.
            transaction_id = str(uuid4())
            transactions['in'][transaction_id] = Transaction(address=remote_address,
                                                             transaction_id=transaction_id)
            #
            save_folder_qml = qmlify_file_path(save_folder)
            # Emit a signal to request the transaction in the main GUI thread.
            self.signal_transaction_requested.emit(remote_address,
                                                   data.get('hostname'),
                                                   data.get('username'),
                                                   data.get('file_name'),
                                                   transaction_id,
                                                   save_folder_qml)
            # Return the transaction ID in a JSON response.
            return jsonify({'transaction_id': transaction_id})
        else:
            return jsonify({'status': 'error'})

    def confirm_transaction(self):
        """
        Confirms a transaction based on the transaction ID received in the request.

        This method processes a request to confirm a transaction. It extracts the transaction ID from the
        request's JSON payload and checks if the transaction exists and is associated with the requesting
        host's address. If the transaction is found, its stage is updated to 'confirmed', and a signal is
        emitted to start the transaction. The method returns a JSON response containing the transaction ID
        if the confirmation is successful, or an error status otherwise.

        Args:
            self: Access to class attributes and methods.

        Returns:
            flask.Response: A JSON response containing the transaction ID if the confirmation is successful,
                            or an error status otherwise.
        """
        data = request.get_json()
        #
        status = 'error'
        transaction_id = data.get('transaction_id')
        # Normalize the remote address to handle IPv4-mapped IPv6 addresses.
        if request.remote_addr.startswith('::ffff:'):
            remote_address = request.remote_addr.split('::ffff:')[1]
        else:
            remote_address = request.remote_addr
        # Check if the transaction exists and is associated with the requesting host.
        if transaction_id and hosts.get(remote_address):
            if transactions['out'].get(transaction_id):
                #
                transactions['out'][transaction_id].stage = 'confirmed'
                self.signal_start_transaction.emit(transaction_id)
                return jsonify({'transaction_id': transaction_id})
        return jsonify({'status': status})

    def cancel_transaction(self):
        """
        Cancels a transaction based on the transaction ID received in the request.

        This method processes a request to cancel a transaction. It extracts the transaction ID from the
        request's JSON payload and checks if the transaction exists and is associated with the requesting
        host's address. If the transaction is found, its stage is updated to 'canceled'. The method returns
        a JSON response containing the status of the operation, which can be 'ok' if the transaction was
        successfully canceled, 'unknown' if the transaction ID does not exist, or 'error' if the host is not
        recognized.

        Args:
            self: Access to class attributes and methods.

        Returns:
            flask.Response: A JSON response containing the status of the cancellation request.
        """
        data = request.get_json()
        # Initialize the status as 'error' by default.
        status = 'error'
        transaction_id = data.get('transaction_id')
        # Normalize the remote address to handle IPv4-mapped IPv6 addresses.
        if request.remote_addr.startswith('::ffff:'):
            remote_address = request.remote_addr.split('::ffff:')[1]
        else:
            remote_address = request.remote_addr
        # Check if the transaction exists and is associated with the requesting host.
        if transaction_id and hosts.get(remote_address):
            if transactions['out'].get(transaction_id):
                transactions['out'][transaction_id].stage = 'canceled'
                status = 'ok'
            else:
                status = 'unknown'
        return jsonify({'status': status})

    def start_transaction(self):
        """
        Processes the start of a file transaction, saving the file sent by the client.

        This method is called to handle the final stage of a file transaction process. It reads the transaction
        details from a JSON file sent by the client, including the transaction ID. It then verifies the transaction
        ID and the client's address, and if valid, saves the file sent by the client to a designated folder. The
        method updates the transaction's stage to 'completed' and returns a JSON response indicating the status
        of the operation.

        Args:
            self: Access to class attributes and methods.

        Returns:
            flask.Response: A JSON response indicating the status of the operation ('ok' for success, 'error' otherwise).
        """
        # Load transaction details from the JSON file sent by the client.
        data = loads(request.files['json'].read().decode('UTF-8'))
        transaction_id = data.get('transaction_id')
        # Initialize the status as 'error' by default.
        status = 'error'
        # Normalize the remote address to handle IPv4-mapped IPv6 addresses.
        if request.remote_addr.startswith('::ffff:'):
            remote_address = request.remote_addr.split('::ffff:')[1]
        else:
            remote_address = request.remote_addr
        # Verify the transaction ID and the client's address.
        if transaction_id and hosts.get(remote_address):
            if transactions['in'].get(transaction_id):
                # Check if a file is attached with the request.
                if request.files.get('file'):
                    # Generate a unique file name to avoid overwriting existing files.
                    unique_file_name = generate_unique_file_name(
                        folder_path=transactions['in'].get(transaction_id).save_folder,
                        file_name=request.files['file'].filename)
                    # Save the file to the designated folder.
                    request.files['file'].save(
                        f"{transactions['in'].get(transaction_id).save_folder}/{unique_file_name}")
                    # Update status to 'ok' to indicate success.
                    status = 'ok'
        # Always set the transaction's stage to 'completed' to ensure it's marked as finished.
        # This happens regardless of the success or failure of the file saving process - if it
        # failed, the transaction will have to be started by the users anyway.
        transactions['in'].get(transaction_id).stage = 'completed'
        # Return a JSON response indicating the status of the operation.
        return jsonify({'status': status})
