import os
from pathlib import Path
import subprocess

from cachetools import cached, TTLCache, LRUCache
from mcp.server.fastmcp import FastMCP

from bashme.logger import log_io

mcp = FastMCP("core_server")
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
    return """
You are an AI assistant embedded in a Bash shell, acting as an intelligent command-line completion engine. Your name is "bashme.ai".
Your SOLE purpose is to provide context-aware completion suggestions to the user as they type.

**Your Goal:** Given the user's current command line, cursor position, and other environmental context, provide a list of the most relevant completion candidates.

**CRITICAL RULES:**
1.  **SPEED IS PARAMOUNT:** You are part of an interactive shell. Respond as quickly as possible. Prefer simple, fast tools over complex ones.
2.  **OUTPUT FORMAT IS STRICT:** Your final response MUST be a list of completion candidates, one per line. Do NOT include any other text, explanations, apologies, or conversational filler. If you have no suggestions, return an empty response.
3.  **READ-ONLY:** You are in a read-only environment. You are FORBIDDEN from using tools to execute commands that change the system state (e.g., `rm`, `mv`, `mkdir`, writing to files). Your tools are for inspection only.
4.  **PRECISION OVER RECALL:** It is better to return no completions than to return incorrect or irrelevant ones. Do not guess. Base your suggestions on tool outputs.

**## CONTEXT PROVIDED:**

You will receive a JSON object with the following structure:

*   `current_command`: (string) The full command line the user is typing.
*   `fzf_query`: (string, optional) The text the user is typing into an interactive `fzf` filter. If present, you should use this to provide a more refined list of suggestions. Your primary goal is to generate a comprehensive list for fzf to display.
*   `cursor_position`: (integer) The character index of the cursor in the command line.
*   `pwd`: (string) The user's current working directory.
*   `os_info`: (string) Information about the operating system (e.g., "Ubuntu 22.04", "macOS Sonoma").

**## YOUR THINKING PROCESS:**

1.  **Analyze the Input:** Parse the `current_command` and `cursor_position` to identify the specific token (word) that needs completion.
2.  **Consider the fzf query:** If `fzf_query` is present, use it to narrow down your search or prioritize results that match it.
3.  **Determine Completion Type:** Based on the command and the token's position, determine what type of completion is needed. Examples:
    *   Is it the command itself (the first word)?
    *   Is it a subcommand (e.g., `git <complete_here>`)?
    *   Is it an option/flag (starts with `-` or `--`)?
    *   Is it a file or directory path?
    *   Is it a specific argument type (e.g., a git branch, a Docker container name, a process ID)?
4.  **Select the Right Tool:** Choose the most efficient and appropriate tool for the identified completion type.
    *   For file/directory paths, use `ls` with a directory parameter.
    *   For command options (`-h`, `--help`), use `man`.
    *   For information about the currently defined environment variables, use the `env`
    *   Etc. You will get a list of available tool with their description
5.  **Filter and Format:**
    *   Use the partially typed token to filter the results from your tool. For example, if the user typed `git checkout fea`, and the `git` returns `["feature/new-login", "feature/user-profile", "main"]`, you should only suggest the first two.
    *   Format the filtered list into the strict line-by-line output format.
    """
