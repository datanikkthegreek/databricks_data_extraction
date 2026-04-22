# Chat endpoint authentication

How the `/api/chat` route authenticates to the Databricks agent endpoint.

## Where the token comes from

1. **OAuth M2M (client_id + client_secret)**  
   If **`DATABRICKS_CLIENT_ID`** and **`DATABRICKS_CLIENT_SECRET`** are both set, the backend uses **OAuth machine-to-machine** for all routes (files, jobs, chat, etc.). No user token or header is required. For chat/SQL the backend obtains an access token from the SDK and uses it for MLflow and the agent endpoint.

2. **When running in Databricks (e.g. Databricks Apps)**  
   If M2M is not set, the platform sends the user’s token in the **`X-Forwarded-Access-Token`** request header.  
   The backend uses this token for all chat calls (MLflow and OpenAI client).

3. **When running locally (no M2M)**  
   If that header is missing or empty, the backend uses the token from **config**:
   - `FEVM_TOKEN`, or
   - `DATA_EXTRACTION_TOKEN`  
   (see `config.py`: `token` is loaded from env with that default).  
   So for local dev you set one of these env vars (e.g. a Databricks PAT) and do **not** need to send `X-Forwarded-Access-Token`.

## How the token is used

- **MLflow path**: Before calling `get_deploy_client("databricks")`, the backend sets:
  - `DATABRICKS_HOST` = `config.host` (e.g. `https://adb-xxx.azuredatabricks.net`)
  - `DATABRICKS_TOKEN` = the token above  
  The MLflow client then uses these to call the Databricks serving API.

- **OpenAI path** (fallback): The `WorkspaceClient` is built with `host=config.host` and `token=<same token>`.  
  `ws.serving_endpoints.get_open_ai_client()` uses that client to call the agent endpoint.

## Requirements for 502 to go away

- The **identity** behind the token (user or service principal) must have **CAN_QUERY** on the agent endpoint (e.g. `mas-2e8563e1-endpoint`).
- For a Multi-Agent Supervisor (MAS), the same permission is needed on any **underlying agent** endpoints the MAS calls (see [Databricks Agent Chat Template](https://github.com/databricks/app-templates/blob/main/e2e-chatbot-app-next/README.md)).

## Seeing the real error when you get 502

- The backend now returns the **exception message(s)** in the 502 response body as `detail` (e.g. `"MLflow client: ...; OpenAI client: ..."` if both paths were tried and failed).
- The **chat UI** shows this `detail` in the red error text under the input when a request fails.
- **Server logs** contain the full traceback for both MLflow and OpenAI client failures (`[CHAT] MLflow agent call failed` and `[CHAT] OpenAI client call failed` with `exc_info=True`).

Check the in-app error text first; then check your backend logs for the full stack trace.

## Required scope: `files`

For **list** and **upload** of files (Files API), the token must have the Databricks **`files`** scope. If you see:

- *"Provided OAuth token does not have required scopes: files"*

then:

- **OAuth / Apps:** Ensure the app’s OAuth client (or the user’s token) is granted the **files** scope in Databricks.
- **PAT (local or fallback):** Create the token in **User Settings → Developer → Access tokens** and enable **Files** (or the scope that includes Files API).

## Auth diagnostic endpoint

**GET /api/auth/diagnostic** (no auth required) returns:

- `header_present`: whether the `x-forwarded-access-token` header is present
- `token_resolved`: whether a token was resolved (header or env fallback)
- `hint`: short explanation

Use this when auth fails on Databricks: open `/api/auth/diagnostic` in the same browser/session as the app. If `header_present` is false, the request is not going through the Databricks Apps proxy (e.g. you opened the app via a direct URL). Fix: open the app from the Databricks Apps launcher.
