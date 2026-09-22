# Connecting JanSaathi to Azure AI Foundry

The app talks to your model through **one file**: `backend/app/services/providers/azure_foundry.py`.
Everything else (search, prompts, privacy filter, fallback, streaming, UI) already works. You only
set environment variables.

It uses the OpenAI-compatible v1 endpoint of your Foundry resource
(`https://<resource>.openai.azure.com/openai/v1/`), which works for models deployed by Azure
(GPT family and others) **and for your own fine-tuned deployments**.

## 1. Get three values from the Foundry portal

1. **Deploy a model** (Models + endpoints -> Deploy). Note the **deployment name** you choose.
   This is what goes into `AZURE_OPENAI_DEPLOYMENT`, not the base model name.
2. Copy the resource **endpoint**, for example `https://my-resource.openai.azure.com/`
   (the `services.ai.azure.com` form also works, the app normalises it).
3. Authentication, pick one:
   - **API key**: copy a key from the resource. Set `AZURE_OPENAI_API_KEY`.
   - **Keyless (recommended for production)**: leave the key empty. The app uses
     `DefaultAzureCredential`: `az login` on your laptop, a managed identity once deployed.
     Give that identity the **Cognitive Services OpenAI User** role on the resource
     (in the portal: Access control (IAM)). If your tenant rejects the default token scope, set
     `AZURE_AI_TOKEN_SCOPE=https://cognitiveservices.azure.com/.default`.

## 2. Configure

In `backend/.env`:
```
AI_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://my-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=my-deployment-name
AZURE_OPENAI_API_KEY=            # blank = Entra ID / managed identity
# Reasoning models (o-series, gpt-5) reject temperature: leave it blank for those.
MODEL_TEMPERATURE=0.2
```
Restart the API. The startup log says which provider is active.

## 3. Verify

```bash
curl http://localhost:8000/api/ai/status
```
`{"ok": true, ...}` means the wiring works. Otherwise the response names the error:

| Symptom | Likely cause |
|---|---|
| `AuthenticationError` / 401 | Wrong key, or the identity lacks the role above |
| `NotFoundError` / 404 | `AZURE_OPENAI_DEPLOYMENT` is not the deployment name, or wrong endpoint |
| `RateLimitError` / 429 | Quota on the deployment. Raise it in Foundry |
| `Falling back to the local provider` in the log | `AI_PROVIDER=azure` but endpoint or deployment is empty |

The app already adapts if a model rejects `temperature` or `max_completion_tokens`
(different model families accept different parameters).

## What happens if Azure fails

Users never see a dead chat. If Azure errors or times out, that answer comes from the local
provider and is marked with a small notice in the UI ("The AI service was busy..."). If the
connection drops halfway through a streamed answer, the partial text stays with an
"interrupted" notice.

## How the model is kept honest

`prompts.py` sends the model only the scheme records our own search selected, and instructs it to
use nothing else: no invented names, amounts, dates or links; "may be eligible" rather than
promises; call 112 for emergencies; ignore instructions inside user messages. Aadhaar, phone,
card and OTP numbers are removed **before** the text reaches the model or any log.
Please still test with your own questions and your own model, since behaviour differs by model.

## Using your own trained model

Deploy it in Foundry, then set `AZURE_OPENAI_DEPLOYMENT` to that deployment's name. No code change.
If your model needs a different prompt format, edit `build_system_prompt()` in `prompts.py`.

## Sensible next steps

- **Azure AI Search** for retrieval once you have hundreds of schemes: replace
  `search.find_relevant()` (same signature).
- **Azure AI Speech** for consistent Punjabi/Hindi voice input and read-aloud on every device
  (the browser features in `hooks/useSpeech.js` vary by device).
- **Key Vault** for the API key, **Application Insights** for monitoring, **Azure Cache for Redis**
  for rate limits if you run several instances (`core/rate_limit.py`).
- **Foundry content safety / evaluations** to test answers before launch.

## Deploying to Azure

The `Dockerfile` in the repo root builds the website and API into a single image:
```bash
docker build -t jansaathi .
docker run -p 8000:8000 --env-file backend/.env jansaathi     # http://localhost:8000
```
Push the image to Azure Container Registry and run it on Azure Container Apps or App Service for
Containers. Set the same environment variables there (store secrets as secrets), enable a managed
identity for keyless auth, and keep `TRUST_PROXY=true`. The Dockerfile was written carefully but
was **not built or run** while this project was prepared, so expect to check it once.
