# 🤖 bashme.ai

**Your AI-powered "Do What I Mean" companion for the command line.**

`bashme.ai` is a smart assistant that lives in your terminal. It analyzes your current, often incomplete, commands or even plain English descriptions, and instantly suggests complete, ready-to-run shell commands. Stop remembering arcane flags and start telling your shell what you want to do.

![Bashme.ai Demo GIF](https://user-images.githubusercontent.com/1423701/299691167-17721867-bb03-4fec-a309-858888b14e30.gif)
*(A sample GIF demonstrating the functionality)*

---

## ✨ Features

*   **🧠 Context-Aware Suggestions:** Uses your current working directory (`ls`), command history (`history`), and even command documentation (`man`) to provide highly relevant and accurate suggestions.
*   **📝 Natural Language to Command:** Simply type a comment like `# find all markdown files modified in the last day` and let the AI generate the precise command for you.
*   **⚡ Interactive & Real-time:** Built with `fzf` for a fluid, real-time filtering experience. Suggestions update live as you refine your query.
*   **🛠️ Agentic Tool Use:** Powered by LangGraph, `bashme.ai` is a true agent. It can decide on its own to use tools like `ls` or `man` to gather information *before* giving you an answer.
*   **🚀 Blazing Fast:** Runs as local daemons to ensure minimal latency, making it feel like a natural part of your shell.
*   **💡 Learns Your Style:** By leveraging your shell history, it adapts to the commands and patterns you use most often.

---

## 🔧 How It Works

`bashme.ai` has a decoupled, client-server architecture to ensure it's both powerful and non-blocking in your shell.

1.  **Shell Integration (`ai_complete.sh` + `fzf`)**: A lightweight Bash script captures your current command line (`$READLINE_LINE`) and cursor position when you press a keybinding (`Alt+c`). It opens an `fzf` window, which provides the interactive UI.
2.  **CLI Client (`cli.py`)**: The `fzf` window calls a simple Python CLI. This client gathers all the context (command, pwd, etc.) and sends it over HTTP to the Agent Daemon.
3.  **Agent Daemon (`agent_daemon.py`)**: A FastAPI server that hosts the LangGraph agent. It receives the context, invokes the agent, and streams the suggestions back to the CLI client, which pipes them into `fzf`.
4.  **Tool Server (`server.py`)**: A `FastMCP` server that exposes crucial functions (`ls`, `man`, `history`, `get_os_info`) as "tools" for the agent. This is how the agent can "see" your local environment to make informed decisions.

![Architecture Diagram](https://user-images.githubusercontent.com/1423701/299691230-67c7e0f2-b0b9-4a92-b43a-7d92ffb1c095.png)

---

## ⚙️ Installation & Setup

Follow these steps to get `bashme.ai` running on your system.

### Prerequisites

*   Linux or macOS with `systemd` (for running services). If you don't use `systemd`, you can run the daemons manually.
*   Python >= 3.11
*   [fzf](https://github.com/junegunn/fzf) (a command-line fuzzy finder)
*   [uv](https://github.com/astral-sh/uv) (an extremely fast Python package installer and resolver)

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/bashme.ai.git
cd bashme.ai
```

### Step 2: Set up the Python Environment

We use `uv` for fast and reliable dependency management.

```bash
# Create a virtual environment
uv venv

# Activate the environment
source .venv/bin/activate

# Install all dependencies from pyproject.toml
uv sync
```

### Step 3: Configure Your API Key

`bashme.ai` uses the Google Gemini API.

1.  Get an API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
2.  Create a configuration directory and an environment file:
    ```bash
    mkdir -p ~/.config/bashme
    cp .env.example ~/.config/bashme/env
    ```
3.  Edit `~/.config/bashme/env` and add your API key:
    ```ini
    # ~/.config/bashme/env
    BASHME_API_KEY=YOUR_GOOGLE_AI_API_KEY_HERE
    ```

### Step 4: Set up the Background Services (Daemons)

We provide `systemd` user services to run the tool server and agent daemon in the background.

1.  **⚠️ IMPORTANT:** The service files contain hardcoded paths. You **must** edit them to match your system.
    *   Find your project path: `pwd` (e.g., `/home/user/bashme.ai`)
    *   Find your python path: `which python` (e.g., `/home/user/bashme.ai/.venv/bin/python`)

2.  Copy the example service files.
    ```bash
    cp bashme_server.service.example bashme_server.service
    cp bashme_agent.service.example bashme_agent.service
    ```

3.  **Edit `bashme_server.service` and `bashme_agent.service`**, replacing all instances of `/home/user/src/bashme.ai` and `/opt/home/user/venv/bashme/bin/python` with your actual paths.

4.  Install and start the services:
    ```bash
    # Create the systemd user directory if it doesn't exist
    mkdir -p ~/.config/systemd/user/

    # Copy the configured service files
    cp bashme_server.service ~/.config/systemd/user/
    cp bashme_agent.service ~/.config/systemd/user/

    # Reload the systemd daemon, then enable and start the services
    systemctl --user daemon-reload
    systemctl --user enable --now bashme_server.service bashme_agent.service
    ```

5.  Check that the services are running:
    ```bash
    systemctl --user status bashme_server.service bashme_agent.service
    ```

### Step 5: Integrate with Your Shell (Bash)

1.  **⚠️ IMPORTANT:** The `ai_complete.sh` script also has hardcoded paths. Edit it to match your environment.
    *   `python_executable` should point to your virtual environment's Python.
    *   `cli_script` should point to the `cli.py` file in the repository.

2.  Once edited, source the script in your `.bashrc` or `.bash_profile` to make it available in your shell sessions.
    ```bash
    # Add this line to the end of your ~/.bashrc
    source /path/to/your/bashme.ai/ai_complete.sh
    ```
3.  Restart your shell or run `source ~/.bashrc`.

---

## 🚀 Usage

You're all set! Now you can use `bashme.ai` in any terminal session.

1.  Start typing a command, or don't type anything at all.
2.  Press **`Alt+c`** (or `Esc` then `c`).
3.  The `fzf` window will appear with AI-generated suggestions.
4.  You can:
    *   Select a command with `Enter`.
    *   Type to filter the suggestions in real-time.
    *   Press `Esc` to cancel.

#### Examples to Try:

*   **Natural Language:** Type `# find all log files in /var/log larger than 10MB` and press `Alt+c`.
*   **Command Completion:** Type `docker run -it pyth` and press `Alt+c`.
*   **Creative Pipelining:** Type `ls -la | # count the number of directories` and press `Alt+c`.
*   **Empty Prompt:** Just press `Alt+c` on an empty line to get suggestions based on your current directory and history (e.g., `git status`).

---

## 🔧 Customization

The heart of the AI's behavior is defined in `src/bashme/system_prompt.xml`. You can edit this file to change the agent's personality, rules, and output format. After editing, simply restart the agent service:

```bash
systemctl --user restart bashme_agent.service
```

## 📜 License

This project is licensed under the GPL-3.0-only License. See the `LICENSE` file for details.

# Personal running notes
```
mkdir /opt/home/user/venv/bashme
ln -s /opt/home/user/venv/bashme .venv

uv sync --all-groups
```

```bash
/opt/home/user/venv/bashme/bin/python /home/user/src/bashme.ai/src/bashme/client.py --current-command "cat ai_"  --cursor-position 7 --pwd $(pwd) --api-key $(vault kv get -mount=secret -field=google_aistudio_api_key airflow)
```

# Server systemd daemon
```bash
mkdir -p ~/.config/bashme ~/.config/systemd/user/
cp bashme_server.service.example bashme_server.service 
cp bashme_agent.service.example bashme_agent.service 
# edit if needed, then
cp bashme_server.service ~/.config/systemd/user/bashme_server.service
cp bashme_agent.service ~/.config/systemd/user/bashme_agent.service
# edit the api key
echo "BASHME_API_KEY=$(vault kv get -mount=secret -field=google_aistudio_api_key airflow)" > .env
cp .env ~/.config/bashme/env
```
