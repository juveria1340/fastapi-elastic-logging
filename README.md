# FastAPI + ELK Logging Pipeline


A project demonstrating structured JSON logging from a FastAPI app, shipped by Filebeat, into Elasticsearch (Elastic Cloud), and explored in Kibana — all orchestrated with a single `docker-compose up`.

## How it works

```
curl request
    -> FastAPI handler (fastapi_elk_app.py)
        -> logger.info(..., extra={...})   # JSON line appended to logs/app.log
            -> Filebeat (filestream input, tailing logs/app.log)
                -> parses each line as JSON, promotes fields to top level
                    -> ships to Elasticsearch (Elastic Cloud) over HTTPS
                        -> searchable/visualizable in Kibana Discover
```

Both the app and Filebeat run as containers defined in `docker-compose.yml`, sharing the `logs/` directory as a volume — the app writes to it, Filebeat reads from it.

## Prerequisites

- Docker Desktop (with Compose v2)
- An Elastic Cloud deployment — [sign up here](https://www.elastic.co/cloud/elasticsearch-service/signup) (free trial available)

## Setup

1. **Get your Elastic Cloud credentials:**
   - Elasticsearch endpoint, e.g. `https://your-deployment.es.us-east-2.aws.elastic-cloud.com:443`
   - An API key: Kibana → Stack Management → API Keys → Create. Note the **id** and **api_key** shown separately (not the base64 "Encoded" value).

2. **Create your `filebeat.yml`** from the template and fill in your credentials:
   ```bash
   cp filebeat.yml.example filebeat.yml
   ```
   Then edit `filebeat.yml`:
   ```yaml
   output.elasticsearch:
     hosts: ["https://your-deployment.es.us-east-2.aws.elastic-cloud.com:443"]
     api_key: "id:api_key"   # plain "id:api_key" format, NOT base64-encoded
   ```
   `filebeat.yml` is gitignored since it holds a live credential — never commit it.

3. **Start everything:**
   ```bash
   docker-compose up -d
   ```
   This builds/starts the FastAPI container (installs deps, runs `fastapi_elk_app.py` on port 8000) and the Filebeat container (tails `logs/app.log`, ships to Elasticsearch).

4. **Stop everything:**
   ```bash
   docker-compose down
   ```

## Generating log data

Hit any endpoint and it's automatically logged, shipped, and indexed within seconds:

```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com"}'

curl http://localhost:8000/users/alice
curl http://localhost:8000/users/999          # 404 case

curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"title":"DevOps Engineer","company":"TechCorp","location":"Remote"}'

curl http://localhost:8000/jobs
```

## Viewing data in Kibana

1. Open Kibana from your Elastic Cloud deployment console.
2. Go to **Discover**.
3. Create/select a data view for index pattern `filebeat-*`, time field `@timestamp`.
4. Widen the time range (e.g. "Last 24 hours") if you don't see results immediately.
5. Expand a document (▸) or add columns like `request_id`, `status_code`, `endpoint`, `response_time_ms`, `job_title` via the field list on the left to see your structured fields — the default columns shown are generic security/ECS fields your app doesn't populate, so they'll appear blank.

## Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

`tests/test_app.py` covers all API endpoints (success and error paths) plus a check that requests actually produce parsable, correctly-fielded JSON log lines — since structured logging is the whole point of this project, not just the API responses.

## Continuous Integration

GitHub Actions (`.github/workflows/ci.yml`) runs on every push/PR to `main`, two jobs:

1. **`lint-and-test`** — `ruff check .` and `pytest tests/`.
2. **`smoke-test`** — spins up the full stack with `docker-compose.ci.yml`, which overrides the Filebeat output to point at a **throwaway local Elasticsearch container** instead of your real Elastic Cloud deployment (config: `filebeat.ci.yml`, no secrets involved). It then posts a real request to the running API and polls the local Elasticsearch until that exact event shows up, proving the whole pipeline — app → log file → Filebeat → Elasticsearch — actually works, not just that each piece starts.

This intentionally never touches your production Elastic Cloud cluster or credentials, so it's safe to run on every push, including from forks/PRs.

## File structure

```
.
├── fastapi_elk_app.py     # FastAPI app with structured JSON logging
├── requirements.txt       # Runtime Python dependencies
├── requirements-dev.txt   # + pytest, httpx, ruff for local dev/CI
├── tests/
│   └── test_app.py        # API + structured-logging tests
├── filebeat.yml.example   # Filebeat config template — copy to filebeat.yml and fill in credentials
├── filebeat.yml           # Your real config with live credentials (gitignored, not tracked)
├── filebeat.ci.yml        # Non-secret Filebeat config used only by the CI smoke test
├── docker-compose.yml     # Orchestrates fastapi-app + filebeat containers
├── docker-compose.ci.yml  # CI override: adds a local Elasticsearch, swaps in filebeat.ci.yml
├── .github/workflows/ci.yml  # Lint + test + smoke-test pipeline
├── .gitignore             # Excludes filebeat.yml, .venv/, logs/, and the vendor binary
├── logs/
│   └── app.log            # Generated JSON log file (shared volume, gitignored)
└── filebeat-9.4.2-windows-x86_64/  # Native Windows Filebeat binary (optional, for running without Docker; gitignored)
```

## Key implementation notes

- **JSON parsing requires `parsers`, not `json.*`.** `filebeat.yml` uses `type: filestream`, which needs JSON decoding configured via a `parsers: [ndjson: ...]` block. The older flat `json.keys_under_root` style only works with the deprecated `type: log` input and is silently ignored under `filestream`.
- **Two different API key formats.** `filebeat.yml`'s `api_key` field wants the plain `id:api_key` string. A raw `curl` `Authorization: ApiKey ...` header wants that same pair **base64-encoded**. Mixing these up produces a `401 Unauthorized`.
- **`filebeat.yml` is gitignored.** It holds a live API key in plaintext, so it's excluded from version control by `.gitignore`. `filebeat.yml.example` is the tracked template — copy it locally and never remove `filebeat.yml` from `.gitignore`.

## Troubleshooting

**Nothing showing in Discover?**
- Check the containers are up: `docker-compose ps`
- Check Filebeat logs: `docker-compose logs filebeat`
- Widen the Discover time range — the most common cause of "no data" is a time filter that excludes recent events.

**Filebeat can't authenticate?**
- Verify `filebeat.yml`'s `api_key` is in plain `id:api_key` form, not base64.
- Regenerate the key in Kibana if it was revoked/expired.

**Data exists but fields look wrong?**
- Confirm `filebeat.yml` uses the `parsers: [ndjson: ...]` block (see above) — without it, entire log lines land as one raw string instead of structured fields.
