# Environment Variables

Certain scripts in this repository rely on environment variables for authentication or service configuration. Prepare these values before running any commands.

| Variable | Description |
| -------- | ----------- |
| `LTI_TOOL_PRIVATE_KEY` | RSA private key or path used to sign LTI launch tokens for KYPO labs. |
| `OPENEDX_URL` | Base URL of the Open edX instance (default `http://localhost:8000`). |
| `OPENEDX_SESSION_COOKIE` | Session cookie for Open edX API calls. Optional when using an API token. |
| `OPENEDX_API_TOKEN` | Token granting access to the Open edX REST API. |
| `OPENEDX_GRADEBOOK_ENDPOINT` | URL template used to push grades to the Open edX gradebook. |
| `OPENEDX_GRADEBOOK_TOKEN` | Token used for gradebook API requests. Defaults to `OPENEDX_API_TOKEN`. |
| `KYPO_URL` | Base URL of the KYPO/CRCZ LTI provider (default `http://localhost:5000`). |
| `LTI_CLIENT_ID` | Client identifier issued by KYPO/CRCZ for the LTI integration. |
| `LTI_DEPLOYMENT_ID` | Deployment identifier for the LTI consumer. |
| `KYPO_LTI_LAUNCH_URL` | Endpoint used to launch KYPO/CRCZ lab sessions via LTI. |
| `MISP_API_KEY` | API key used to authenticate to MISP when fetching or pushing CTI data. The startup scripts mask this value in logs and console output to avoid leaking it. |
| `MISP_URL` | Base URL of the MISP instance (default `http://localhost:8443`). |

Example setup:

```bash
export LTI_TOOL_PRIVATE_KEY=$(cat /path/to/key.pem)
export OPENEDX_URL='https://openedx.example'
export MISP_API_KEY='your-misp-key'
```

Adjust these values as needed for your environment.

To confirm the configured value without exposing it in clear text, compare a masked version against your source (for example, `printenv MISP_API_KEY | sed -E 's/.{0,4}$/****&/'`) or check only the last few characters with `${MISP_API_KEY: -4}` in an interactive shell.
