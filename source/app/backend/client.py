# Client part of FileSwoosh
# © 2024 Henri Wahl

from json import JSONDecodeError, dumps
from socket import AF_INET6

from flask import Response
import httpx
from multicast_expert import McastRxSocket
from PyQt6.QtCore import QThread, pyqtSlot

from ..config import MULTICAST_ADDRESS, PORT, HOSTNAME, USERNAME
from ..helpers import get_default_interface_ipv6_list, get_link_local_address_of_ipv4_default_route, deqmlify_file_path, \
    get_host_info
from ..storage import link_local_address_cache, transactions, Transaction

# Initialize an HTTP client with specific configurations to avoid using the environment's proxy settings,
# disable SSL verification, and set a timeout of 30 seconds.
http_client = httpx.Client(trust_env=False,
                           verify=False,
                           timeout=30)


class SimpleResponse:
    """
    A simple wrapper class for handling HTTP responses.

    Attributes:
        data (dict): The JSON-decoded data from the HTTP response.
        headers (dict): The headers from the HTTP response.

    Methods:
        __init__(response: Response): Initializes the SimpleResponse object with data and headers from the given response.
    """

    data: dict
    headers: dict

    def __init__(self, response: Response = None):
        """
        Initializes the SimpleResponse object with data and headers from the given response.

        Args:
            response (Response, optional): The HTTP response to wrap. Defaults to None.
        """
        self.data = response.json() if response else {}
        self.headers = response.headers if response else {}


class ClientThread(QThread):
    """
    A thread to handle client-side multicast listening and connection initiation.

    This thread listens for multicast packets on a specified IPv6 address and port. Upon receiving a packet,
    it checks if the source address is a link-local address and not already cached. If not cached, it caches
    the address with its scope ID and initiates a connection to the sender.

    Attributes:
        Inherits from QThread.
    """

    def run(self):
        """
        The main execution method of the thread.

        Gathers the default interface IPv6 addresses or, if not available, the link-local address of the IPv4
        default route. It then listens for multicast packets on these addresses. Upon receiving a packet, it
        caches the sender's address if it's a link-local address and not already cached, then initiates a
        connection to the sender.
        """
        # Get the default interface IPv6 addresses or the link-local address of the IPv4 default route if none.
        interface_ips = get_default_interface_ipv6_list()
        if not interface_ips:
            interface_ips = [get_link_local_address_of_ipv4_default_route()]

        # Listen for multicast packets on the specified IPv6 address and port.
        with McastRxSocket(addr_family=AF_INET6, mcast_ips=[MULTICAST_ADDRESS], port=PORT,
                           iface_ips=interface_ips, timeout=None) as rx_socket:
            while True:
                recv_result = rx_socket.recvfrom(1024)
                if recv_result is not None:
                    packet, address_port_tuple = recv_result
                    address = address_port_tuple[0]
                    scope_id = address_port_tuple[3]
                    # Cache the sender's address if it's a link-local address and not already cached.
                    if address.startswith('fe80:') and not link_local_address_cache.get(address):
                        link_local_address_cache[address] = f'{address}%{scope_id}'
                        address = link_local_address_cache[address]
                    # Initiate a connection to the sender.
                    self.connect(address)

    def connect(self, remote_address: str = ''):
        """
        Initiates a connection to a remote address.

        This method prepares and sends a connection request to the specified remote address. It gathers host
        information using the `get_host_info` function and sends this data as part of the connection request.

        Args:
            remote_address (str): The IPv6 address of the remote host to connect to.

        Note:
            The actual connection logic, including error handling and response processing, is implemented in the
            `request` method. This method simply prepares and forwards the connection data.
        """
        self.request(remote_address=remote_address,
                     remote_call='connect',
                     data=get_host_info())

    def request(self,
                remote_address: str = '',
                remote_call: str = '',
                data: dict = None,
                files: dict = None):
        """
        Sends a request to a specified remote address with optional data and files.

        This method constructs a URL based on the provided remote address and remote call, then sends a POST request
        using the httpx client. If the remote address is a link-local IPv6 address without a scope ID, it attempts
        to retrieve the scope ID from cache. The method handles both IPv6 and IPv4 addresses and supports sending
        JSON data and files as part of the request. On success, it returns a SimpleResponse object wrapping the
        response. In case of a JSON decode error or any other exception, it logs the error and returns None. It
        ensures that any files opened are closed in a finally block.

        Args:
            remote_address (str): The IPv6 or IPv4 address of the remote host. For link-local IPv6 addresses,
                                  the scope ID is appended if not already present.
            remote_call (str): The specific endpoint or function to call on the remote host.
            data (dict, optional): A dictionary of data to send as JSON in the request body.
            files (dict, optional): A dictionary where keys are the file field names and values are open file
                                    objects to send with the request.

        Returns:
            SimpleResponse or None: A SimpleResponse object wrapping the HTTP response on success, or None if
                                    there was an error with the request or JSON decoding.
        """
        # Check if the remote address is a link-local IPv6 address without a scope ID and retrieve it from cache if available
        if remote_address.startswith('fe80:') and \
                '%' not in remote_address and \
                link_local_address_cache.get(remote_address):
            remote_address = link_local_address_cache.get(remote_address)
        try:
            # Construct the URL based on the remote address and call
            if ':' in remote_address:
                url = f'https://[{remote_address}]:{PORT}/{remote_call}'
            else:
                url = f'https://{remote_address}:{PORT}/{remote_call}'
            # Send the POST request with the provided data and files
            response = http_client.post(url=url,
                                        json=data,
                                        files=files)
            # Check for successful response status
            if response and \
                    response.status_code == httpx.codes.OK:
                try:
                    # Return a SimpleResponse object wrapping the response
                    return SimpleResponse(response=response)
                except JSONDecodeError:
                    # Log and return None on JSON decode error
                    print('JSON decode error:', response.text)
                    return None
        except Exception as error:
            # Log and return None on any connection error
            print(f'Connection error from {remote_address}: "{error}"')
            return None
        finally:
            # Ensure any opened files are closed
            if files and files.get('file'):
                files['file'].close()

    @pyqtSlot(str, str)
    def request_transaction(self, remote_address: str = '', file_path=''):
        """
        Initiates a transaction request to a remote address with a specified file.

        This method prepares and sends a transaction request to the specified remote address. It includes
        the hostname, username, and the name of the file intended for the transaction. Upon receiving a
        successful response containing a transaction ID, it registers the transaction in the local
        transactions dictionary with the 'out' key, indicating an outgoing transaction.

        Args:
            remote_address (str): The IPv6 or IPv4 address of the remote host. For link-local IPv6 addresses,
                                  the scope ID should be appended.
            file_path (str): The path to the file intended for the transaction. This path is cleaned and
                             processed to extract the file name.

        Decorators:
            @pyqtSlot(str, str): Indicates that this method is a slot that can be connected to signals
                                 in Qt. It accepts two strings as arguments.
        """
        # Clean the file path from QML URL formatting.
        file_path = deqmlify_file_path(file_path)

        # Prepare and send the transaction request.
        response = self.request(remote_address=remote_address,
                                remote_call='request-transaction',
                                data={'hostname': HOSTNAME,
                                      'username': USERNAME,
                                      'file_name': file_path.name})
        # If a transaction ID is received, register the transaction.
        if response and response.data.get('transaction_id'):
            transaction_id = response.data['transaction_id']
            transactions['out'][transaction_id] = Transaction(
                address=remote_address,
                file_path=file_path,
                transaction_id=transaction_id)

    @pyqtSlot(str, str)
    def confirm_transaction(self, transaction_id: str = '', save_folder_updated: str = ''):
        """
        Confirms a transaction and optionally updates the save folder for the transaction.

        This method is triggered to confirm a transaction with a given ID. If a new save folder is provided,
        it updates the save folder for this transaction. It then sends a confirmation request to the remote
        address associated with the transaction.

        Args:
            transaction_id (str, optional): The ID of the transaction to confirm. Defaults to an empty string.
            save_folder_updated (str, optional): The new save folder path, if updating is needed. Defaults to an empty string.

        Decorators:
            @pyqtSlot(str, str): Indicates that this method is a slot that can be connected to signals in Qt.
                                 It accepts two strings as arguments, for the transaction ID and the updated save folder path.
        """
        # Access the global save folder.
        global save_folder
        # Check if the transaction exists in the incoming transactions dictionary.
        if transactions['in'].get(transaction_id):
            remote_address = transactions['in'][transaction_id].address
            # If a new save folder is provided, update the global save folder and the transaction's save folder.
            if save_folder_updated:
                save_folder = deqmlify_file_path(save_folder_updated)
                transactions['in'].get(transaction_id).save_folder = deqmlify_file_path(save_folder_updated)

            # Send a confirmation request to the remote address with the transaction ID.
            self.request(remote_address=remote_address,
                         remote_call='confirm-transaction',
                         data={'transaction_id': transaction_id})

    @pyqtSlot(str)
    def cancel_transaction(self, transaction_id: str = ''):
        """
        Cancels a transaction identified by its transaction ID.

        This method is designed to cancel an requested transaction. It checks if the transaction exists in the
        incoming transactions dictionary. If found, it sends a cancellation request to the remote address associated
        with the transaction. Upon successful cancellation, it updates the transaction's stage to 'canceled'.

        Args:
            transaction_id (str, optional): The ID of the transaction to be canceled. Defaults to an empty string.

        Decorators:
            @pyqtSlot(str): Indicates that this method is a slot that can be connected to signals in Qt.
                            It accepts a single string argument for the transaction ID.
        """
        if transactions['in'].get(transaction_id):
            remote_address = transactions['in'][transaction_id].address
            #
            self.request(remote_address=remote_address,
                         remote_call='cancel-transaction',
                         data={'transaction_id': transaction_id})
            transactions['in'].get(transaction_id).stage = 'canceled'

    @pyqtSlot(str)
    def start_transaction(self, transaction_id: str = ''):
        """
        Initiates the start of a transaction for a confirmed transaction ID.

        This method checks if the transaction with the given ID exists in the 'out' transactions dictionary and
        if its stage is 'confirmed'. If so, it opens the file associated with the transaction in binary read mode
        and prepares a dictionary with the file and transaction ID as JSON. It then sends a request to start the
        transaction to the remote address associated with this transaction. Upon successful request, it updates
        the transaction's stage to 'completed'.

        Args:
            transaction_id (str, optional): The ID of the transaction to start. Defaults to an empty string.

        Decorators:
            @pyqtSlot(str): Indicates that this method is a slot that can be connected to signals in Qt.
                            It accepts a single string argument for the transaction ID.
        """
        if transactions['out'].get(transaction_id):
            transaction = transactions['out'][transaction_id]
            if transaction.stage == 'confirmed':
                remote_address = transactions['out'][transaction_id].address
                files = {'file': open(transaction.file_path, 'rb'),
                         'json': dumps({'transaction_id': transaction_id})}
                self.request(remote_address=remote_address,
                             remote_call='start-transaction',
                             files=files)
                transactions['out'].get(transaction_id).stage = 'completed'