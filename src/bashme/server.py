import os
from pathlib import Path
import subprocess
import logging

from cachetools import cached, TTLCache, LRUCache
from fastmcp import FastMCP

from bashme.logger import log_io

logger = logging.getLogger(__name__)
transport = "http"
port = 50051
mcp = FastMCP("bashme_core")
ttl_cache = TTLCache(maxsize=1024, ttl=5)
lru_cache = LRUCache(maxsize=1024)


@mcp.tool()
@log_io
@cached(ttl_cache)
def ls(path: str) -> list[str]:
    """Lists the files and directories directly within a given path.

    This function takes a path to a directory and returns a list of
    pathlib.Path objects, each representing a file or subdirectory inside it.
    It does not recurse into subdirectories.

    Args:
        path: The path to the directory to list. Can be a string
            or a Path-like object.

    Returns:
        A list of pathlib.Path objects for each item in the directory.
        An empty list is returned for an empty directory or if the input is not a directory
    """
    # Create a Path object for robust and cross-platform path handling.
    directory_path = Path(path)
    # Validate that the path exists.
    if not directory_path.exists() or not directory_path.is_dir():
        return []

    # Use iterdir() to get an iterator of all items in the directory
    #    and convert it to a list.
    return [str(x) for x in directory_path.iterdir()]


@mcp.resource("bash://man/{command_name}")
@log_io
@cached(lru_cache)
def man(command_name: str) -> str:
    """Fetches the man page for a given command.

    This function executes the `man` command in a subprocess and captures
    its output. It is designed to be safe and handle common errors gracefully.

    Note:
        This function requires the `man` command to be installed and available
        in the system's PATH. It will not work on systems without it (e.g.,
        standard Windows installations).

    Args:
        command_name (str): The name of the command for which to retrieve
            the man page (e.g., "ls", "grep").

    Returns:
        str: The content of the man page as a single string if it is found.
             An empty string if the man page does not exist or if the `man`
             command itself cannot be run.
    """

    command: list[str] = ["man", command_name]
    try:
        # Run the 'man' command.
        # - `capture_output=True`: Captures stdout and stderr.
        # - `text=True`: Decodes stdout/stderr from bytes into strings using
        #   the default encoding.
        # - We do not use `check=True` because we want to handle the non-zero
        #   exit code from `man` (which indicates "page not found") ourselves.
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            env={
                "MANPAGER": "cat"
            },  # Prevents `man` from opening an interactive pager like `less`
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return ""
    except FileNotFoundError:
        # This exception occurs if the `man` command itself is not found
        # in the system's PATH.
        # print("Error: The 'man' command is not installed or not in the PATH.")
        return ""


@mcp.tool()
@log_io
@cached(ttl_cache)
def history(n: int) -> list[str]:
    """
    Fetches the last n valid commands from the user's shell history.

    This function locates the history file by first checking the `$HISTFILE`
    environment variable. If the variable is not set, it defaults to
    `~/.bash_history`. It then reads the file, ignoring any comments (lines
    starting with '#') and blank lines, to return a list of the n most
    recent valid commands in chronological order.

    Args:
        n (int): The number of recent valid commands to retrieve.

    Returns:
        List[str]: A list of the last n commands. The list will be shorter
            if the history contains fewer than n valid commands. It returns
            an empty list if n <= 0, the history file cannot be found, or
            the file contains no valid commands.
    """
    # 1. Handle invalid input for n
    if n <= 0:
        return []

    # 2. Determine the history file location
    histfile_env = os.environ.get("HISTFILE")
    if histfile_env:
        # Use the path from the environment variable. expanduser() handles '~'
        histfile_location = Path(histfile_env).expanduser()
    else:
        # Fallback to the default bash history location
        histfile_location = Path.home() / ".bash_history"

    # 3. Check if the history file exists
    if not histfile_location.is_file():
        print(f"Warning: History file not found at '{histfile_location}'")
        return []

    # 4. Read the file and find the last n valid commands
    valid_commands = []
    try:
        # Read all lines into memory. 'errors="ignore"' is safe for history files.
        with open(histfile_location, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()

        # Iterate through lines in reverse to find the most recent commands first
        for line in reversed(all_lines):
            # We have enough commands, so we can stop searching
            if len(valid_commands) == n:
                break

            stripped_line = line.strip()
            # A valid command is non-empty and not a comment
            if stripped_line and not stripped_line.startswith("#"):
                valid_commands.append(stripped_line)

        # The list is in reverse chronological order, so reverse it back
        valid_commands.reverse()
        return valid_commands

    except (IOError, OSError) as e:
        print(f"Error reading history file '{histfile_location}': {e}")
        return []


@mcp.tool()
@log_io
@cached(ttl_cache)
def env() -> dict[str, str]:
    """Retrieves a copy of all current environment variables.

    This function accesses the environment variables of the current process
    and returns them as a standard Python dictionary. By returning a copy,
    it ensures that any modifications made to the returned dictionary do not
    affect the live process environment.

    Returns:
        A dictionary where keys are the environment variable names (str)
        and values are their corresponding string values. The dictionary
        is a snapshot and is disconnected from the live environment.
    """
    # os.environ is a special mapping object that reflects the live environment.
    # To return a disconnected snapshot, we convert it to a standard dict.
    # This is the safest and most common practice.
    return dict(os.environ)


@mcp.prompt("system_prompt")
@log_io
def system_prompt() -> str:
    return open(Path(__file__).parent / "system_prompt.xml").read()


if __name__ == "__main__":
    log_level = "INFO"
    logger.info(f"Starting bashme.ai server on {transport}://localhost:{port}...")
    try:
        mcp.run(transport="http", host="localhost", port=port, log_level=log_level)
    except KeyboardInterrupt:
        logger.info("\nShutting down server...")
