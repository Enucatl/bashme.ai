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
