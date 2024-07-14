# Configuration of some basic parameters for FileSwoosh
# © 2024 Henri Wahl

from getpass import getuser
from pathlib import Path
from platform import system
from socket import gethostname
import sys

# Conditional import for Windows-specific functionality for getting username
if system() == 'Windows':
    import ctypes
else:
    # Import for Unix/Linux systems to get user information
    from pwd import getpwnam


def get_full_username(login: str) -> str:
    """
    Retrieve the full username for a given login name.

    On Windows, this function uses the Windows API to get the full name of the user.
    On Unix/Linux, it retrieves the full name from the user's password database entry.

    Args:
        login (str): The login name of the user.

    Returns:
        str: The full name of the user.
    """
    full_username = login
    if system() == 'Windows':
        # Use Windows API to get the full username
        get_user_name_ex_w = ctypes.windll.secur32.GetUserNameExW
        name_display = 3
        size = ctypes.pointer(ctypes.c_ulong(0))
        # First call to get the size of the buffer needed
        get_user_name_ex_w(name_display, None, size)
        # Allocate buffer for the full username
        name_buffer = ctypes.create_unicode_buffer(size.contents.value)
        # Second call to get the full username
        get_user_name_ex_w(name_display, name_buffer, size)
        if name_buffer.value:
            full_username = name_buffer.value
    else:
        # Get full name from the Unix/Linux user's password database entry
        if getpwnam(login).pw_gecos:
            full_username = getpwnam(login).pw_gecos.rstrip(',')
    return full_username


# Configuration constants
 # Port number for network communication, arbitrary value in the range 49152–65535 which
 # is not used by any known service
PORT: int = 56934
# Multicast address for network communication, using hexadecimal value of port number
# part of network address
MULTICAST_ADDRESS = f'ff05::dead:beef:cafe:{PORT:04x}'

# User and system information
# Current user's login name
LOGIN = getuser()
# Full name of the current user
USERNAME = get_full_username(LOGIN)
# Hostname of the current system, using first label of FQDN
HOSTNAME = gethostname().split('.')[0]

# time-to-live setting for detected hosts in seconds
TIME_TO_LIVE = 15
# Current operating system platform
PLATFORM = system()

# Determine the root directory of the application - this is needed to correctly access the resources directory
if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
    # Running in a bundled environment by PyInstaller
    ROOT_DIR = Path(sys._MEIPASS)
else:
    # Running in a normal Python environment
    ROOT_DIR = Path(__file__).parent.parent.absolute()