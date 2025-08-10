import os
import sys
import httpx
import click


@click.command()
@click.option("--host", default="localhost")
@click.option("--port", type=int, default=50052)
@click.option("--current-command", required=True)
@click.option("--fzf-query", default=None)
@click.option("--cursor-position", required=True, type=int)
@click.option("--pwd", required=True)
def main(host, port, current_command, fzf_query, cursor_position, pwd):
    """
    A lightweight CLI that sends the shell context to the running agent daemon.
    """
    agent_daemon_url = f"http://{host}:{port}/generate"

    payload = {
        "current_command": current_command,
        "fzf_query": fzf_query,
        "cursor_position": cursor_position,
        "pwd": pwd,
        "histfile": os.environ.get("HISTFILE"),
        "path": os.environ.get("PATH"),
    }

    try:
        with httpx.Client() as client:
            response = client.post(agent_daemon_url, json=payload, timeout=10.0)
            response.raise_for_status()

            data = response.json()
            suggestions = data.get("suggestions", [])

            # Print each suggestion on a new line for fzf
            for suggestion in suggestions:
                print(suggestion)

    except httpx.RequestError as e:
        # Print a helpful error message to stderr so fzf ignores it for choices
        print(f"Error connecting to bashme agent daemon: {e}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
