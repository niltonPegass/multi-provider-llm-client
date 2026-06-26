# Building LLM API Clients in Python — A Hands-on Guide

## Part 2 — The Gemini SDK

> Chapters 4, 5, and 6
> Covers: authentication, generation parameters, and your first API call in detail

---

# Chapter 4: Authentication and the Client Object

## 4.1 What is Authentication?

**Authentication** is the process of proving your identity to a system. When you call the Gemini API, Google needs to know:

1. **Who are you?** — to know which account to associate the request with
2. **Are you allowed?** — to check your quota and billing status
3. **How much have you used?** — to enforce rate limits

All three questions are answered by a single value: your **API key**.

Authentication is distinct from **authorization** — a subtlety worth understanding:

| Concept | Question answered | Example |
|---|---|---|
| Authentication | Who are you? | Your API key identifies your account |
| Authorization | What are you allowed to do? | Your account tier determines which models you can use |

An API key simultaneously authenticates (identifies you) and authorizes (determines your permissions based on your account).

---

## 4.2 How API Key Authentication Works

Every HTTP request to the Gemini API carries your key in a **request header**:

```
x-goog-api-key: AIzaSy-YOUR-KEY-HERE
```

The server reads this header on every request, validates it against its database of registered keys, and either proceeds or returns a `403 PERMISSION_DENIED` error.

You never write this header manually — the SDK adds it automatically when you pass `api_key=` to the client constructor. But knowing it exists is important for debugging: if you ever use a tool like `curl` or an HTTP client to test the API directly, you need to add this header yourself.

---

## 4.3 The Old SDK vs. The New SDK

Understanding why the authentication approach changed helps you read older code you will find online.

**Old SDK (`google-generativeai`, deprecated):**

```python
import google.generativeai as genai

# Configures authentication globally — a "side effect"
genai.configure(api_key=API_KEY)

# All subsequent calls use the globally configured key
model = genai.GenerativeModel("gemini-pro")
response = model.generate_content("Hello")
```

The problem with global configuration:
- Calling `genai.configure()` modifies a module-level variable that all code in the process shares.
- If two parts of your program need different API keys (e.g., different Google accounts), they interfere with each other.
- In automated tests, you cannot easily swap in a fake client — the global state persists between tests.

**New SDK (`google-genai`, current):**

```python
from google import genai

# Creates an explicit client object — no global state
client = genai.Client(api_key=API_KEY)

# The key is bound to this specific client instance
response = client.models.generate_content(model=MODEL, contents="Hello")
```

The client object carries its own state — specifically, the API key and any HTTP configuration. Multiple client objects can coexist with different keys. This is **explicit over implicit**, one of Python's core design principles (documented in `import this`).

---

## 4.4 The Factory Function Pattern

In `gemini/client.py`, authentication is handled by a **factory function**:

```python
def create_client() -> genai.Client:
    return genai.Client(api_key=API_KEY)
```

A factory function is a regular function whose sole job is to build and return an object. This might seem like unnecessary indirection — why not just call `genai.Client(api_key=API_KEY)` directly wherever you need a client?

The answer is **change containment**. Consider these scenarios:

**Scenario A:** Google adds a required `project_id` parameter to the client.

Without a factory, you find and update every `genai.Client(...)` call across all files.
With a factory, you update one line in `client.py`.

**Scenario B:** You want to add logging every time a client is created.

Without a factory, you add the logging call everywhere.
With a factory, you add it once inside `create_client()`.

**Scenario C:** You want to test `operations.py` with a fake client that doesn't make real API calls.

Without a factory, the real `genai.Client` is hardcoded in `operations.py`.
With a factory, you can replace `create_client` with a test double in your test setup.

The factory pattern is a specific instance of the broader principle: **program to the place where decisions are made, not where they are used**.

---

## 4.5 The genai.Client Object

When `create_client()` runs, it returns an instance of `genai.Client`. This object is the gateway to all Gemini API operations.

```python
client = genai.Client(api_key=API_KEY)

# The client exposes namespaced sub-resources:
client.models          # model-related operations
client.files           # file upload/management
client.caches          # context caching

# The call we use most:
client.models.generate_content(...)      # synchronous generation
client.models.generate_content_stream(...)  # streaming generation
client.models.list()                     # list available models
```

The `.models` attribute is itself an object (sometimes called a "service object" or "resource object"). This namespacing keeps the client's API surface organized — you don't have thirty methods directly on `client`, you have a few namespaced groups.

---

## 4.6 What Happens When Authentication Fails?

When the API key is wrong, missing, or has been revoked, Google returns HTTP `403`. The SDK raises this as `gemini_errors.ClientError`.

In `_handle_error()` in `errors.py`:

```python
if isinstance(error, gemini_errors.ClientError):
    code = str(error)
    if "403" in code or "PERMISSION_DENIED" in code:
        return {
            "success": False,
            "response": "Authentication error: check your API_KEY in config.py.",
            "error_type": "ClientError_403"
        }
```

Why check `str(error)` for `"403"`?

The SDK uses a single `ClientError` class for all 4xx errors. The HTTP status code is embedded in the exception's string representation. We convert the error to a string with `str(error)` and check whether `"403"` appears in it — a pragmatic approach that works reliably even as the SDK's internal structure evolves.

---

# Chapter 5: Generation Parameters

## 5.1 What is GenerateContentConfig?

Every API call to generate content accepts a `config` parameter — an instance of `types.GenerateContentConfig`. This object bundles all the "how should the model respond?" settings into one place.

In `gemini/client.py`:

```python
def create_config(**overrides) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=overrides.get("temperature", TEMPERATURE),
        max_output_tokens=overrides.get("max_output_tokens", MAX_TOKENS),
    )
```

And in `operations.py`, it is passed as `config=`:

```python
response = client.models.generate_content(
    model=MODEL,
    contents=prompt,
    config=config,        # ← the GenerateContentConfig object
)
```

Let's examine each parameter in depth.

---

## 5.2 The `model` Parameter

```python
MODEL: str = "models/gemini-2.5-flash"
```

This string tells the API which specific model version to route your request to. Several things about this parameter are worth understanding:

**Why the `models/` prefix?**

The new `google-genai` SDK uses the full resource path as the model identifier, following Google's API naming conventions. The path `models/gemini-2.5-flash` means "the resource named `gemini-2.5-flash` under the `models` collection." The older SDK and some documentation omit the prefix — this is why model names without `models/` return a `404 NOT_FOUND` error with the new SDK.

**Model families and naming:**

```
gemini-2.5-flash        ← family: gemini-2.5, variant: flash
gemini-2.5-flash-lite   ← same family, lighter variant
gemini-2.5-pro          ← same family, more capable variant
```

The naming pattern:
- **Family** (e.g., `2.5`): the generation of the model architecture
- **Variant** (e.g., `flash`, `pro`): the capability/cost tier within that generation

`flash` models are optimized for speed and cost.
`pro` models are optimized for capability.
`lite` variants are smaller, faster, and cheaper than their base counterparts.

**Why model selection matters:**

Different models have different:
- Capabilities (reasoning depth, instruction following, code generation quality)
- Context windows (maximum tokens they can process)
- Costs (tokens per dollar)
- Speed (tokens per second)
- Rate limits (requests per minute on the free tier)

For a learning project, `gemini-2.5-flash` is the right default — it is capable enough to give meaningful responses and has a generous free tier.

---

## 5.3 Temperature: Controlling Randomness

```python
TEMPERATURE: float = 0.3
```

Temperature is one of the most important and most misunderstood LLM parameters.

**The technical explanation:**

LLMs generate text one token at a time. At each step, the model computes a probability distribution over its entire vocabulary — every possible next token gets a score. Temperature modifies this distribution before sampling.

At `temperature = 0.0`:
The model always picks the token with the highest probability. Given the same input, it produces identical output every time. This is called **greedy decoding**.

At `temperature > 0.0`:
The distribution is "softened" — lower probability tokens become relatively more likely. The higher the temperature, the more the model explores alternatives. At very high temperatures, even unlikely tokens get sampled regularly, which can produce creative but incoherent output.

**A practical mental model:**

Think of the model choosing the next word from a bag of options. At temperature 0, it always picks the most common one. At temperature 1, it picks roughly in proportion to how common each option is. At temperature 2, it reaches into the bag more randomly.

**Gemini's scale:**

The Gemini API accepts temperatures from `0.0` to `2.0`. Most providers cap at `1.0` or `2.0`. Values above `1.0` are rarely useful for technical tasks.

**Practical guide:**

| Use case | Recommended temperature |
|---|---|
| Code generation | 0.0 – 0.2 |
| Technical Q&A, factual answers | 0.2 – 0.4 |
| General conversation, explanations | 0.4 – 0.7 |
| Creative writing, brainstorming | 0.7 – 1.2 |
| Experimental / artistic | 1.2 – 2.0 |

Our project uses `0.3` — appropriate for technical responses that should be accurate and consistent but not robotically identical on repeated calls.

**An experiment worth running:**

Ask the same creative question five times with `temperature = 0.0` and five times with `temperature = 1.5`. The difference in output variety will make the parameter's effect immediately intuitive.

---

## 5.4 max_output_tokens: Controlling Response Length

```python
MAX_TOKENS: int = 2048
```

`max_output_tokens` is a hard ceiling on how many tokens the model can generate in a single response. When the model reaches this limit, it stops generating — even mid-sentence.

**What it is NOT:**

- It is not a target length. The model generates as much as it needs to, up to the limit.
- It is not a token budget that you "pay for upfront." You only pay for tokens actually generated.

**Stop reasons:**

When generation ends, the response includes a `finish_reason`:

```python
response.candidates[0].finish_reason
```

| Value | Meaning |
|---|---|
| `STOP` | Model finished naturally (most common) |
| `MAX_TOKENS` | Hit the `max_output_tokens` limit mid-response |
| `SAFETY` | Response was blocked by safety filters |
| `RECITATION` | Response contained copyrighted material |

If you are seeing truncated responses, check if `finish_reason` is `MAX_TOKENS` and increase the limit.

**Relationship to the context window:**

Every model has a total context window — the maximum number of tokens it can process in one call (input + output combined). If your input prompt is very long (say, 50,000 tokens), and `max_output_tokens` is 2,048, the total is within limits. But if you set `max_output_tokens` to 1,000,000, the API will reject it — the context window is finite.

---

## 5.5 The System Prompt (system_instruction)

```python
SYSTEM_PROMPT: str = """
You are a friendly technical assistant with a concise, direct writing style.
...
""".strip()
```

The system prompt is a persistent behavioral directive delivered to the model before any user message. It defines:

- **Persona:** what role the model plays
- **Tone:** how formal or casual its writing should be
- **Constraints:** what it should or should not do
- **Format preferences:** prose vs. lists, language, length

**Why it is not a conversation turn:**

In the new Gemini SDK, the system prompt is passed as `system_instruction` inside `GenerateContentConfig` — a configuration object, not a message. It is processed by the model differently from user messages, with higher weight and persistence throughout the conversation.

This is different from the older pattern (and from some other providers) where the system prompt was injected as the first message in the conversation array with `role: "system"`.

**The practical effect:**

Without a system prompt, the model behaves as a generic assistant. With a well-crafted system prompt, you get a specialized tool. The same model with two different system prompts can feel like completely different applications.

**Example — same question, different system prompts:**

System prompt A:
```
You are a patient teacher explaining concepts to a ten-year-old.
```

System prompt B:
```
You are a senior ML engineer. Be concise, use correct technical terminology,
and skip introductory context.
```

Question: "What is gradient descent?"

System prompt A produces an analogy about rolling a ball downhill.
System prompt B produces a formal definition with convergence conditions.

**Writing effective system prompts:**

1. **Be specific about role.** "You are a technical assistant" is vague. "You are a Data Science assistant helping a senior analyst prepare for technical interviews" is precise.

2. **Specify format preferences.** "Prefer flowing prose over bullet lists" or "Always use code blocks for code examples."

3. **Set language and tone.** "Respond in Portuguese" or "Use formal academic language."

4. **State what NOT to do** when relevant. "Do not speculate. If you are uncertain, say so."

5. **Keep it focused.** A system prompt that tries to do everything does nothing well.

---

## 5.6 The **overrides Pattern in create_config()

```python
def create_config(**overrides) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=overrides.get("temperature", TEMPERATURE),
        max_output_tokens=overrides.get("max_output_tokens", MAX_TOKENS),
    )
```

**What is `**kwargs`?**

`**overrides` (the double asterisk) is Python syntax that collects any keyword arguments passed to the function into a dictionary. The name after `**` is arbitrary — `**kwargs`, `**options`, `**overrides` all work the same way.

```python
def create_config(**overrides):
    print(overrides)

create_config()
# prints: {}

create_config(temperature=0.9)
# prints: {"temperature": 0.9}

create_config(temperature=0.9, max_output_tokens=512)
# prints: {"temperature": 0.9, "max_output_tokens": 512}
```

Inside the function, `overrides` is a regular Python dictionary.

**What is `.get(key, default)`?**

`dict.get(key, default)` retrieves the value for `key` if it exists, or returns `default` if it does not. This is safer than `dict[key]`, which raises `KeyError` when the key is missing.

```python
overrides = {"temperature": 0.9}

overrides.get("temperature", TEMPERATURE)
# → 0.9  (key exists, returns its value)

overrides.get("max_output_tokens", MAX_TOKENS)
# → 2048 (key missing, returns the default from config.py)
```

Combined, `**overrides` + `.get(key, default)` implements **optional parameter overriding** — a clean pattern for functions that have sensible defaults but allow caller customization:

```python
# Uses all defaults from config.py
config = create_config()

# Overrides only temperature; max_output_tokens still uses config.py default
config = create_config(temperature=1.2)

# Overrides both
config = create_config(temperature=0.0, max_output_tokens=256)
```

---

# Chapter 6: Making Your First API Call

## 6.1 The Full Lifecycle of a Request

Let's trace exactly what happens when `main.py` calls `safe_chat("What is a transformer?")`:

```
main.py
  calls safe_chat("What is a transformer?")
    ↓
gemini/errors.py — safe_chat()
  calls simple_chat("What is a transformer?")
    ↓
gemini/operations.py — simple_chat()
  calls create_client()
    ↓
gemini/client.py — create_client()
  returns genai.Client(api_key="AIzaSy...")
    ↑
  calls create_config()
    ↓
gemini/client.py — create_config()
  returns GenerateContentConfig(temperature=0.3, max_output_tokens=2048, ...)
    ↑
  calls client.models.generate_content(model=MODEL, contents=prompt, config=config)
    ↓
[HTTP POST to Google's servers — network round trip]
    ↓
  returns response object
  returns response.text → "A transformer is a deep learning architecture..."
    ↑
gemini/errors.py — safe_chat()
  wraps in dict: {"success": True, "response": "A transformer is...", "error_type": None}
    ↑
main.py
  prints result["response"]
```

Every function call you make ultimately results in one HTTP request and one HTTP response. The layers above it (factories, wrappers, safe functions) are all Python — no network involved until `generate_content()` is called.

---

## 6.2 The Response Object in Detail

`client.models.generate_content()` returns a `GenerateContentResponse` object. Let's look at its structure:

```python
response = client.models.generate_content(
    model=MODEL,
    contents="What is the difference between supervised and unsupervised learning?",
    config=config,
)

# The shortcut — what we use in the project
response.text
# → "Supervised learning uses labeled data..."

# The full path to the same value
response.candidates[0].content.parts[0].text
# → "Supervised learning uses labeled data..."

# Token usage — useful for monitoring costs
response.usage_metadata.prompt_token_count      # → 12
response.usage_metadata.candidates_token_count  # → 187
response.usage_metadata.total_token_count       # → 199

# Why generation stopped
response.candidates[0].finish_reason
# → "STOP"  (finished naturally)
```

**What is `candidates`?**

The API can generate multiple candidate responses in a single call (controlled by a `candidate_count` parameter). By default, `candidate_count = 1`, so `candidates` is a list with one item — accessed as `candidates[0]`. Using `response.text` is equivalent to `response.candidates[0].content.parts[0].text` and is the standard approach when you have one candidate.

**What is `content.parts`?**

The content of a response is a list of `Part` objects. For plain text responses, there is always exactly one part with a `.text` attribute. The list structure exists because a response can theoretically contain multiple content types (text, images, function calls) in one turn.

---

## 6.3 Reading the Token Usage

After every call, `response.usage_metadata` tells you exactly how many tokens were consumed. This is important for:

1. **Cost estimation.** Tokens × price per million tokens = cost.
2. **Context window monitoring.** If `prompt_token_count` grows large (from long conversations), you may approach the model's limit.
3. **Debugging.** If a response seems truncated, compare `candidates_token_count` to `max_output_tokens`.

A simple logging wrapper:

```python
def simple_chat_with_logging(prompt: str) -> str:
    client = create_client()
    config = create_config()

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=config,
    )

    # Log token usage
    usage = response.usage_metadata
    print(f"[Tokens] input: {usage.prompt_token_count} | "
          f"output: {usage.candidates_token_count} | "
          f"total: {usage.total_token_count}")

    return response.text
```

---

## 6.4 Running list_models.py — What It Does and Why

```python
from google import genai
from config import API_KEY

client = genai.Client(api_key=API_KEY)

for model in client.models.list():
    print(f"  {model.name}")
```

`client.models.list()` makes a `GET` request to the Gemini API's model listing endpoint and returns an iterable of model objects. Each object has a `.name` attribute — the exact string you must use in `config.py`.

**Why run this before starting?**

Model availability changes over time and varies by account tier. What is available on one account or region may not be available on another. Running this script takes one second and saves you from mysterious `404 NOT_FOUND` errors.

**What the `for` loop does:**

```python
for model in client.models.list():
    print(f"  {model.name}")
```

`client.models.list()` returns an **iterator** — not a pre-built list, but an object that yields one model at a time as you loop. Python's `for` loop works with any iterator: it calls the iterator's `__next__()` method on each iteration until the iterator signals it is exhausted.

This is memory-efficient: if there were thousands of models, the iterator would fetch them in batches rather than loading all into memory at once.

---

## 6.5 The Synchronous Call in Full Context

Here is `simple_chat()` with every line annotated:

```python
def simple_chat(prompt: str) -> str:
    # Create a new authenticated client for this call
    # (one client per call is slightly inefficient but simple and safe)
    client = create_client()

    # Bundle the generation parameters
    config = create_config()

    # Make the API call — this is the only line that touches the network.
    # Execution blocks here until Google's server responds.
    response = client.models.generate_content(
        model=MODEL,          # which model to use — from config.py
        contents=prompt,      # the user's message as a string
        config=config,        # temperature, max_output_tokens, system_instruction
    )

    # response.text extracts just the generated text from the response object.
    # It is equivalent to: response.candidates[0].content.parts[0].text
    return response.text
```

**"Synchronous" vs. "Asynchronous":**

`simple_chat()` is **synchronous** — when it calls `generate_content()`, the entire Python thread waits (blocks) until the response arrives. Nothing else runs during that wait.

Python also supports **asynchronous** programming (`async`/`await`), which allows other tasks to run while waiting for slow operations like network calls. The Gemini SDK supports async, but we use synchronous calls here — they are simpler to understand and sufficient for a learning project.

When you move to building web APIs (e.g., with FastAPI) where many users might make requests simultaneously, the async version becomes important. That is covered in Part 6.

---

## 6.6 One Client Per Call vs. One Shared Client

In the current project, `create_client()` is called inside each operation function:

```python
def simple_chat(prompt: str) -> str:
    client = create_client()   # new client every call
    ...
```

This means a new `genai.Client` object is created for every API call. In practice, this is slightly wasteful — creating a client is cheap but not free.

A more efficient pattern for applications that make many calls is to create one client at startup and reuse it:

```python
# At application startup
_client = create_client()

def simple_chat(prompt: str) -> str:
    config = create_config()
    response = _client.models.generate_content(...)
    return response.text
```

The project uses the per-call pattern because:
1. It is simpler and eliminates questions about when/where the client is initialized.
2. For a learning project making occasional calls, the overhead is negligible.
3. It avoids the complexity of managing shared state between functions.

Understanding this trade-off — simplicity vs. efficiency — is important as you move toward production code.

---

## Part 2 Summary

| Concept | One-line summary |
|---|---|
| API key authentication | Sent as HTTP header `x-goog-api-key` on every request |
| `genai.Client` | Explicit client object — the gateway to all API operations |
| Factory function | A function that builds and returns an object; centralizes construction logic |
| `model` parameter | Exact resource path string identifying which LLM version to use |
| Temperature | Controls randomness: 0.0 = deterministic, 2.0 = very creative |
| `max_output_tokens` | Hard ceiling on response length; only generated tokens are billed |
| System prompt | Persistent behavioral instruction sent before any user message |
| `**overrides` / `**kwargs` | Collects arbitrary keyword arguments into a dictionary |
| `.get(key, default)` | Safe dict lookup — returns default if key is missing |
| `response.text` | Shortcut for the model's generated text in the response object |
| `finish_reason` | Why generation stopped: STOP, MAX_TOKENS, SAFETY, RECITATION |
| Synchronous call | Execution blocks until the full response arrives |

---

*Next: Part 3 — Communication Patterns (Chapters 7, 8, and 9)*
*Synchronous calls in depth, streaming via SSE, and multi-turn conversations.*

