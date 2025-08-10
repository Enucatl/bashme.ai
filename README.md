# bashme.ai
An AI bash companion

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
