# Helpful variables and functions for FileSwoosh
# © 2024 Henri Wahl

from pathlib import Path
from socket import AF_INET, AF_INET6
from typing import Optional, List

import netifaces
from multicast_expert import get_default_gateway_iface_ip_v6

from app.config import HOSTNAME, USERNAME, PLATFORM

# Determine the default save folder - use the Downloads folder in the user's home directory if existent
save_folder = Path.home() / 'Downloads' if (Path.home() / 'Downloads').exists() else Path.home()
# Define the file URL prefix based on the operating system
file_url_prefix = 'file:///' if PLATFORM == 'Windows' else 'file://'


def get_link_local_address_of_ipv4_default_route() -> str:
    """
    Retrieves the link-local IPv6 address associated with the default IPv4 gateway.

    This function queries the system's network interfaces and gateways to find the
    default IPv4 gateway and then looks up its associated link-local IPv6 address.

    This is a fallback in case hosts do not have full IPv6 connectivity, but can still
    access link local addresses.

    Returns:
        str: The link-local IPv6 address of the default IPv4 gateway, or None if not found.
    """
    default_gateway_interface_ipv6 = None
    gateways = netifaces.gateways()
    #
    default_gateway_ipv4 = gateways.get('default')
    if default_gateway_ipv4:
        #
        default_gateway_interface = default_gateway_ipv4[AF_INET][1]
        default_gateway_interface_addresses = netifaces.ifaddresses(default_gateway_interface)
        # Find the first link-local IPv6 address
        default_gateway_interface_ipv6 = default_gateway_interface_addresses[AF_INET6][0]['addr']
    return default_gateway_interface_ipv6


def get_default_interface_ipv6_list() -> Optional[List[str]]:
    """
    Retrieves a list of IPv6 addresses for the default network interface.

    This function finds the default network interface for IPv6 traffic and returns
    a list of its non-link-local IPv6 addresses.

    Returns:
        Optional[List[str]]: A list of IPv6 addresses, or None if the default interface or addresses are not found.
    """
    gateways = netifaces.gateways()
    #
    if not 'default' in gateways or not AF_INET6 in gateways['default']:
        return None

    default_gateway = gateways['default'][AF_INET6]
    default_gateway_interface = default_gateway[1]
    interface_addresses = netifaces.ifaddresses(default_gateway_interface)

    # Filter out link-local addresses and return the rest
    ipv6_addresses = [info['addr'] for addr_family, addr_info in interface_addresses.items()
                      if addr_family == AF_INET6
                      for info in addr_info
                      if 'addr' in info and not info['addr'].startswith('fe80:')]
    return ipv6_addresses


def get_default_address() -> str:
    """
    Retrieves the default network address for the host.

    This function first attempts to get the default IPv6 address using the gateway interface.
    If no default IPv6 address is found, it falls back to retrieving the link-local IPv6 address
    associated with the default IPv4 gateway.

    Returns:
        str: The default network address.
    """
    default_address = get_default_gateway_iface_ip_v6()
    #
    if not default_address:
        default_address = get_link_local_address_of_ipv4_default_route()
    return default_address


def get_host_info() -> dict:
    """
    Constructs a dictionary with basic host information.

    This function gathers the default network address, hostname, and username of the host,
    packaging them into a dictionary.

    Returns:
        dict: A dictionary containing 'address', 'hostname', and 'username' of the host.
    """
    return {'address': get_default_address(),
            'hostname': HOSTNAME,
            'username': USERNAME}


def deqmlify_file_path(file_path: str) -> Path:
    """
    Cleans and converts a file path URL to a Path object.

    This function removes the 'file://' or 'file:///' prefix from a file path URL and
    returns a Path object representing the file path.

    Args:
        file_path (str): The file path URL to clean.

    Returns:
        Path: The cleaned file path as a Path object.
    """
    if file_path.startswith(file_url_prefix):
        return Path(file_path.split(file_url_prefix)[1])
    else:
        return Path(file_path)


def qmlify_file_path(file_path: Path) -> str:
    """
    Converts a file path to a format suitable for QML.

    This function ensures the file path is in a URL format that QML can use, especially
    necessary for Windows paths which are converted to forward slashes and prefixed with 'file:///'.

    Args:
        file_path (Path): The file path to convert.

    Returns:
        str: The file path in a QML-friendly format.
    """
    file_path_string = str(file_path)
    file_path_string = file_path_string.replace('\\', '/')
    # Add the file URL prefix if not already present
    if not file_path_string.startswith('file:'):
            return file_url_prefix + file_path_string
    else:
        return file_path_string

def generate_unique_file_name(folder_path: Path, file_name: str) -> str:
    """
    Generates a unique file name within a specified directory.

    If the given file name already exists in the directory, appends a counter to the file name
    until a unique name is found. The counter is incremented and appended to the original file name
    base, preserving the file extension.

    Args:
        folder_path (Path): The directory in which to check for uniqueness.
        file_name (str): The desired file name.

    Returns:
        str: A unique file name within the specified directory.
    """
    file_path = folder_path / file_name
    # If the file does not exist, return the original file name
    if not file_path.exists():
        return file_name

    counter = 1
    while True:
        # Append a counter to the file name until a unique name is found
        new_file_name = f"{file_path.stem}_{counter}{file_path.suffix}"
        new_file_path = folder_path / new_file_name
        # Break the loop when a unique file name is found
        if not new_file_path.exists():
            break
        counter += 1
    return new_file_name


def get_all_addresses() -> List[str]:
    """
    Retrieves all non-local IP addresses of the host.

    This function iterates over all network interfaces.
    It collects both IPv4 and IPv6 addresses, excluding loopback addresses (::1, 127.0.0.1).

    Returns:
        List[str]: A list of non-local IP addresses.
    """
    all_addresses = list()
    #
    for interface in netifaces.interfaces():
        # Check IPv4 as well as IPv6 addresses
        for address_family in [AF_INET, AF_INET6]:
            if address_family in netifaces.ifaddresses(interface):
                # Filter out link-local and loopback addresses
                for address in netifaces.ifaddresses(interface)[address_family]:
                    if not address['addr'] in ['::1', '127.0.0.1']:
                        all_addresses.append(address['addr'])
    return all_addresses


def get_all_addresses_filtered() -> List[str]:
    """
    Retrieves all non-local and non-link-local IP addresses of the host.

    This function iterates over all network interfaces, excluding those typically associated
    with virtual networks (e.g., Docker, virtual bridges). It collects both IPv4 and IPv6 addresses,
    excluding link-local (fe80::/10 for IPv6) and loopback addresses (::1, 127.0.0.1).

    Returns:
        List[str]: A list of non-local and non-link-local IP addresses.
    """
    all_addresses_filtered = list()
    #
    for interface in netifaces.interfaces():
        if not interface.startswith('docker') and not interface.startswith('virbr'):
            # Check IPv4 as well as IPv6 addresses
            for address_family in [AF_INET, AF_INET6]:
                if address_family in netifaces.ifaddresses(interface):
                    # Filter out link-local and loopback addresses
                    for address in netifaces.ifaddresses(interface)[address_family]:
                        if not address['addr'].startswith('fe80:') and not address['addr'] in ['::1', '127.0.0.1']:
                            all_addresses_filtered.append(address['addr'])
    return all_addresses_filtered

def get_all_addresses_filtered_as_text() -> str:
    """
    Retrieves all non-local and non-link-local IP addresses of the host as a newline-separated string.

    Utilizes `get_all_addresses` to fetch the addresses and then joins them into a single string,
    separated by double newlines for readability.

    Returns:
        str: A newline-separated string of non-local and non-link-local IP addresses.
    """
    return '\n\n'.join(get_all_addresses_filtered())