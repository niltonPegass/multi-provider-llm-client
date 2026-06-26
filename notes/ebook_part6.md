# Building LLM API Clients in Python — A Hands-on Guide

## Part 6 — Putting It All Together

> Chapters 17, 18, and 19
> Covers: reading the full project top-to-bottom, how to extend it,
> and what to study next

---

# Chapter 17: Reading the Full Project Top to Bottom

## 17.1 Why Read Code You Already Wrote?

There is a significant difference between code you produced incrementally
(writing one function at a time, debugging as you go) and code you read as a
complete system. Reading your own project from scratch — as if seeing it for
the first time — is one of the most effective ways to consolidate understanding.

This chapter walks through every file in the project in dependency order,
connecting each piece to the concepts from earlier parts. By the end, you
should be able to explain any line of this codebase to someone else — which
is exactly the level of understanding that holds up in technical interviews.

---

## 17.2 Reading Order

Always read code in dependency order — from the most fundamental (no
dependencies) to the most derived (depends on everything else):

```
1. my_api_keys.py     ← no dependencies
2. config.py          ← depends on my_api_keys.py
3. gemini/client.py   ← depends on config.py
4. gemini/operations.py ← depends on client.py
5. gemini/errors.py   ← depends on operations.py
6. gemini/__init__.py ← re-exports from errors, operations, client
7. list_models.py     ← depends on config.py (standalone utility)
8. main.py            ← depends on gemini/ package
```

---

## 17.3 my_api_keys.py

```python
MY_GOOGLE_API_KEY = "AIzaSy-YOUR-KEY-HERE"
```

**What it is:** A one-line secret store. The simplest possible file.

**Why it exists as a separate file:** So it can be added to `.gitignore` and
never committed to version control. Every other file in the project can be
public; this one cannot.

**What to notice:** No type hint here. That is fine — the file is so simple
that the type is obvious from the value. Type hints provide the most value
when functions and modules interact with each other; a single assignment
in an isolated file gains little from annotation.

**Interview talking point:** "Secrets are separated from logic in a dedicated
file excluded from version control. In production, I would replace this with
environment variables or a secrets manager."

---

## 17.4 config.py

```python
from my_api_keys import MY_GOOGLE_API_KEY

API_KEY: str = MY_GOOGLE_API_KEY
MODEL: str = "models/gemini-2.5-flash"
MAX_TOKENS: int = 2048
TEMPERATURE: float = 0.3
SYSTEM_PROMPT: str = """...""".strip()
```

**What it is:** The single source of truth for all tunable parameters.

**What to notice:**

The `from my_api_keys import MY_GOOGLE_API_KEY` line is the only place
in the entire project where the secret is read. Every other file that needs
the key imports `API_KEY` from `config.py` — not from `my_api_keys.py` directly.
This creates one indirection layer, which means you could change the secret
storage mechanism (switch to environment variables, for example) by modifying
only this one line.

`SYSTEM_PROMPT` uses a triple-quoted string with `.strip()`. The triple quotes
allow multi-line content without escape characters. `.strip()` removes the
leading newline that appears right after the opening `"""`.

The constants are written in `UPPER_SNAKE_CASE`. This is the Python convention
for module-level constants — it signals "this value is not meant to be changed
at runtime."

**Interview talking point:** "All configuration lives in one file. Changing
the model, temperature, or system behavior requires editing one place and
nothing else."

---

## 17.5 gemini/client.py

```python
from google import genai
from google.genai import types
from config import API_KEY, SYSTEM_PROMPT, TEMPERATURE, MAX_TOKENS

def create_client() -> genai.Client:
    return genai.Client(api_key=API_KEY)

def create_config(**overrides) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=overrides.get("temperature", TEMPERATURE),
        max_output_tokens=overrides.get("max_output_tokens", MAX_TOKENS),
    )
```

**What it is:** The authentication and configuration factory layer.

**What to notice:**

`create_client()` is four lines including the `def` and `return`. It does
exactly one thing: create an authenticated client. The simplicity is the point —
simple functions are easy to test, easy to replace, and easy to reason about.

`create_config(**overrides)` uses the parameterized factory pattern. The
`**overrides` dict starts empty when called with no arguments, making `.get()`
return the config.py defaults. With keyword arguments, it returns overridden values.

Both functions are **pure factories** — they take inputs, build objects, return them.
No side effects, no I/O, no modification of external state.

**The import `from config import ...`** explicitly lists what is needed.
This is preferable to `import config` (which imports the whole module) because
it makes dependencies explicit and readable.

**Interview talking point:** "Factory functions centralize object construction.
If the SDK's Client constructor changes, I update one function — not every
place a client is created."

---

## 17.6 gemini/operations.py

```python
from google.genai import types
from .client import create_client, create_config
from config import MODEL

def simple_chat(prompt: str) -> str:
    client = create_client()
    config = create_config()
    response = client.models.generate_content(
        model=MODEL, contents=prompt, config=config,
    )
    return response.text

def stream_chat(prompt: str, callback=None) -> str:
    client = create_client()
    config = create_config()
    full_text = ""
    for chunk in client.models.generate_content_stream(
        model=MODEL, contents=prompt, config=config,
    ):
        full_text += chunk.text
        if callback:
            callback(chunk.text)
        else:
            print(chunk.text, end="", flush=True)
    return full_text

def multi_turn_chat(history: list, new_message: str) -> tuple[str, list]:
    client = create_client()
    config = create_config()
    history.append(
        types.Content(role="user", parts=[types.Part(text=new_message)])
    )
    response = client.models.generate_content(
        model=MODEL, contents=history, config=config,
    )
    response_text = response.text
    history.append(
        types.Content(role="model", parts=[types.Part(text=response_text)])
    )
    return response_text, history
```

**What it is:** The API call layer — the only place in the project where
network requests happen.

**What to notice:**

`from .client import ...` is a relative import — the dot means "same package
(`gemini/`)." This is correct inside a package and avoids hardcoding the
package name.

All three functions follow the same structure:
1. Create client and config
2. Make the API call
3. Return results

None of them have error handling. That is deliberate — error handling is the
next layer's responsibility. These functions do one thing: communicate with
the API.

`stream_chat()` introduces two patterns not present in `simple_chat()`:
- An **iterator** (`for chunk in generate_content_stream(...)`)
- A **callback** parameter (optional function called per chunk)

`multi_turn_chat()` introduces **list mutation** (`.append()` modifying
`history` in place) and a **tuple return** (`return response_text, history`).

**Interview talking point:** "Operations are isolated from error handling.
I can test API behavior directly by calling these functions, and I can test
error handling separately by mocking them."

---

## 17.7 gemini/errors.py

```python
from google.genai import errors as gemini_errors
from .operations import simple_chat, stream_chat, multi_turn_chat

def _handle_error(error: Exception) -> dict:
    if isinstance(error, gemini_errors.ClientError):
        code = str(error)
        if "403" in code or "PERMISSION_DENIED" in code:
            return {"success": False, "response": "Authentication error...", "error_type": "ClientError_403"}
        if "429" in code or "RESOURCE_EXHAUSTED" in code:
            return {"success": False, "response": "Rate limit...", "error_type": "ClientError_429"}
        return {"success": False, "response": f"Request error (4xx): {error}", "error_type": "ClientError"}
    if isinstance(error, gemini_errors.ServerError):
        return {"success": False, "response": f"Server error (5xx): {error}", "error_type": "ServerError"}
    return {"success": False, "response": f"Unexpected error: {error}", "error_type": "UnexpectedError"}

def safe_chat(prompt: str) -> dict:
    try:
        return {"success": True, "response": simple_chat(prompt), "error_type": None}
    except Exception as e:
        return _handle_error(e)

def safe_stream_chat(prompt: str, callback=None) -> dict:
    try:
        text = stream_chat(prompt, callback)
        return {"success": True, "response": text, "error_type": None}
    except Exception as e:
        return _handle_error(e)

def safe_multi_turn_chat(history: list, new_message: str) -> dict:
    history_copy = list(history)
    try:
        response_text, updated_history = multi_turn_chat(history_copy, new_message)
        return {"success": True, "response": response_text, "history": updated_history, "error_type": None}
    except Exception as e:
        result = _handle_error(e)
        result["history"] = history
        return result
```

**What it is:** The error handling layer — wraps operations in try/except
and returns structured results.

**What to notice:**

`_handle_error()` is the DRY pivot point. All three wrappers route their
exceptions through it. The underscore prefix signals it is internal.

The three safe wrappers are structurally identical except for one thing:
`safe_multi_turn_chat()` pre-creates `history_copy = list(history)` before
the try block. This is outside the try because the copy must exist in the
except block (to return the unmodified original history on failure).

`result["history"] = history` in the except block adds a key to an existing
dict — the dict was created by `_handle_error()` without a `"history"` key,
and we add it after the fact.

**Interview talking point:** "The safe wrappers implement a Result pattern —
every call returns a dict with `success: bool` rather than raising. This keeps
the presentation layer free of try/except logic."

---

## 17.8 gemini/__init__.py

```python
from gemini.errors import safe_chat, safe_stream_chat, safe_multi_turn_chat
from gemini.operations import simple_chat, stream_chat, multi_turn_chat
from gemini.client import create_client, create_config

__all__ = [
    "safe_chat", "safe_stream_chat", "safe_multi_turn_chat",
    "simple_chat", "stream_chat", "multi_turn_chat",
    "create_client", "create_config",
]
```

**What it is:** The package's public interface declaration.

**What to notice:**

This file does not define any new logic. Its entire purpose is to re-export
names from sub-modules, making them accessible as `from gemini import safe_chat`
instead of `from gemini.errors import safe_chat`.

`__all__` lists every name intentionally exposed to callers. Anything not
listed (like `_handle_error`) remains accessible but is marked as internal
by convention.

The import order here (errors first, then operations, then client) is the
reverse of the dependency order. This is fine — by the time `__init__.py`
runs these imports, all sub-modules are already loaded in the correct
dependency order through the cascading import chain.

**Interview talking point:** "`__init__.py` acts as an abstraction boundary.
Callers depend on the package's public API, not on which internal file
each function lives in. Internal restructuring doesn't break external code."

---

## 17.9 main.py

```python
from gemini import safe_chat, safe_stream_chat, safe_multi_turn_chat

def header(title: str) -> None: ...
def footer(info: str = "") -> None: ...

def demo_simple_chat() -> None:
    header("DEMO 1 — Simple Chat")
    while True:
        prompt = input("\nYour question (or /bye to exit): ")
        if prompt.strip().lower() == "/bye":
            break
        result = safe_chat(prompt)
        if result["success"]:
            print(f"\nResponse:\n{result['response']}")
        else:
            print(f"\nError [{result['error_type']}]: {result['response']}")
    footer()

def demo_streaming() -> None: ...
def demo_multi_turn() -> None: ...

if __name__ == "__main__":
    demos = {"1": demo_simple_chat, "2": demo_streaming, "3": demo_multi_turn}
    choice = input("\nEnter the demo number: ").strip()
    if choice in demos:
        demos[choice]()
    else:
        print(f"Invalid choice: '{choice}'. Please enter 1, 2, or 3.")
```

**What it is:** The presentation and entry point layer.

**What to notice:**

`main.py` imports only from `gemini` — not from `gemini.errors` or
`gemini.operations`. It depends on the package's public interface, not
its internals. This is the abstraction boundary working as intended.

The demo functions contain no API logic — only `input()`, `print()`, and
`if/else` on the result dict. The hard work happens in the layers below.

The `while True` / `break` pattern is idiomatic Python for interactive loops.
`prompt.strip().lower() == "/bye"` normalizes user input before comparing —
`"  /BYE  "`, `"/Bye"`, and `"/bye"` all match.

The dispatch table `{"1": demo_simple_chat, ...}` and `demos[choice]()`
is the cleanest way to route string input to functions without a chain of
`if/elif`. The `if choice in demos` guard prevents a `KeyError` on invalid input.

**Interview talking point:** "The entry point has zero API knowledge. It
receives structured results from the gemini package and renders them. Swapping
Gemini for another provider only requires changing the import line."

---

## 17.10 The Project as a System

With all files read, here is the system view:

```
┌─────────────────────────────────────────────────────────────┐
│  User types in terminal                                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  main.py  (presentation)                                     │
│  • Interactive loops, input(), print()                       │
│  • Dispatch table for demo selection                         │
│  • No API logic, no error handling                           │
└──────────────────────────┬──────────────────────────────────┘
                           │  from gemini import safe_*
┌──────────────────────────▼──────────────────────────────────┐
│  gemini/ package  (business logic)                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ errors.py  — safe wrappers, _handle_error()            │ │
│  │ • Never raises, always returns dict                    │ │
│  │ • Routes exceptions through _handle_error()            │ │
│  └──────────────────────────┬─────────────────────────────┘ │
│                             │  calls                         │
│  ┌──────────────────────────▼─────────────────────────────┐ │
│  │ operations.py  — API calls                              │ │
│  │ • simple_chat(), stream_chat(), multi_turn_chat()       │ │
│  │ • May raise ClientError or ServerError                  │ │
│  └──────────────────────────┬─────────────────────────────┘ │
│                             │  calls                         │
│  ┌──────────────────────────▼─────────────────────────────┐ │
│  │ client.py  — factories                                  │ │
│  │ • create_client(), create_config()                      │ │
│  │ • Reads from config.py                                  │ │
│  └──────────────────────────┬─────────────────────────────┘ │
└──────────────────────────── │ ────────────────────────────── ┘
                              │  HTTP over internet
┌─────────────────────────────▼───────────────────────────────┐
│  Google Gemini API  (external service)                       │
│  • Authenticates request, generates tokens, returns response │
└─────────────────────────────────────────────────────────────┘
```

Every arrow in this diagram is an import or a function call.
Every box has exactly one responsibility.
Data flows downward; results flow upward.

---

# Chapter 18: How to Extend This Project

## 18.1 The Extension Points

A well-designed project has clear extension points — places where new
functionality can be added without disturbing what already works.
This project has four:

1. **New providers** — adding OpenAI, Anthropic, or other LLM APIs
2. **New operation modes** — adding function calling, vision, embeddings
3. **New interface layers** — adding a web API, a CLI tool, a Slack bot
4. **New configuration** — adding per-request system prompts, per-user settings

---

## 18.2 Extension 1 — Adding a Second Provider (Anthropic)

The project structure anticipates this: `gemini/` is a provider-specific package.
Adding Anthropic means creating an `anthropic/` package with the same public interface.

**Step 1: Create `anthropic/` with identical structure:**

```
anthropic/
├── __init__.py
├── client.py      ← create_client() using anthropic.Anthropic(api_key=...)
├── operations.py  ← simple_chat(), stream_chat(), multi_turn_chat()
└── errors.py      ← safe_chat(), safe_stream_chat(), safe_multi_turn_chat()
```

**Step 2: Implement `anthropic/client.py`:**

```python
import anthropic as anthropic_sdk
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, MAX_TOKENS, TEMPERATURE, SYSTEM_PROMPT

def create_client() -> anthropic_sdk.Anthropic:
    return anthropic_sdk.Anthropic(api_key=ANTHROPIC_API_KEY)

def create_config(**overrides) -> dict:
    return {
        "model": overrides.get("model", ANTHROPIC_MODEL),
        "max_tokens": overrides.get("max_tokens", MAX_TOKENS),
        "temperature": overrides.get("temperature", TEMPERATURE),
    }
```

**Step 3: Implement `anthropic/operations.py`:**

```python
from .client import create_client, create_config
from config import ANTHROPIC_MODEL, SYSTEM_PROMPT

def simple_chat(prompt: str) -> str:
    client = create_client()
    cfg = create_config()
    response = client.messages.create(
        model=cfg["model"],
        max_tokens=cfg["max_tokens"],
        temperature=cfg["temperature"],
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
```

Key Anthropic differences to handle:
- `client.messages.create()` instead of `client.models.generate_content()`
- `system=` is a top-level parameter, not inside config
- History uses `{"role": "assistant", ...}` not `"model"`
- Streaming uses `client.messages.stream()` context manager

**Step 4: Update `main.py` to choose provider:**

```python
# Option A: import based on a config setting
PROVIDER = "gemini"   # or "anthropic"

if PROVIDER == "gemini":
    from gemini import safe_chat, safe_stream_chat, safe_multi_turn_chat
else:
    from anthropic import safe_chat, safe_stream_chat, safe_multi_turn_chat

# Everything below this line is unchanged — same interface, different provider
```

This is the power of the abstraction boundary: `main.py` does not know or care
which provider is active. The same interactive loops work with either.

---

## 18.3 Extension 2 — Adding Function Calling

**Function calling** (also called "tool use") lets the model request that your
code execute a specific function and return the result. This is the foundation
of AI agents.

Example flow:
```
User:  "What's the weather in Rio de Janeiro right now?"
Model: [requests tool call: get_weather(city="Rio de Janeiro")]
Code:  executes get_weather("Rio de Janeiro") → {"temp": 28, "condition": "sunny"}
Model: "It's currently 28°C and sunny in Rio de Janeiro."
```

To add this to `operations.py`:

```python
from google.genai import types

# Define tools the model can call
TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="get_weather",
                description="Get current weather for a city",
                parameters=types.Schema(
                    type="object",
                    properties={
                        "city": types.Schema(type="string", description="City name")
                    },
                    required=["city"]
                )
            )
        ]
    )
]

def chat_with_tools(prompt: str) -> str:
    client = create_client()
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=TEMPERATURE,
        max_output_tokens=MAX_TOKENS,
        tools=TOOLS,
    )

    response = client.models.generate_content(
        model=MODEL, contents=prompt, config=config
    )

    # Check if the model wants to call a function
    candidate = response.candidates[0]
    if candidate.content.parts[0].function_call:
        fn_call = candidate.content.parts[0].function_call
        fn_name = fn_call.name
        fn_args = dict(fn_call.args)

        # Execute the function locally
        if fn_name == "get_weather":
            result = get_weather(fn_args["city"])   # your implementation

        # Send the result back to the model
        follow_up = client.models.generate_content(
            model=MODEL,
            contents=[
                types.Content(role="user", parts=[types.Part(text=prompt)]),
                types.Content(role="model", parts=[candidate.content.parts[0]]),
                types.Content(role="user", parts=[
                    types.Part(function_response=types.FunctionResponse(
                        name=fn_name, response={"result": result}
                    ))
                ]),
            ],
            config=config
        )
        return follow_up.text

    return response.text
```

This extension goes into `operations.py` as a new function. `errors.py` gets
a corresponding `safe_chat_with_tools()` wrapper. `main.py` gets a
`demo_function_calling()` and an entry in the dispatch table.

---

## 18.4 Extension 3 — Adding a FastAPI Web Interface

Replacing the terminal menu with a web API that other applications can call.

**Install FastAPI:**

```bash
pip install fastapi uvicorn
```

**Create `api.py`:**

```python
from fastapi import FastAPI
from pydantic import BaseModel
from gemini import safe_chat, safe_stream_chat
from fastapi.responses import StreamingResponse

app = FastAPI()

class ChatRequest(BaseModel):
    prompt: str

class ChatResponse(BaseModel):
    success: bool
    response: str
    error_type: str | None

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    result = safe_chat(request.prompt)
    return ChatResponse(**result)

@app.post("/chat/stream")
def chat_stream(request: ChatRequest):
    def token_generator():
        for chunk in []:   # placeholder — real streaming needs async
            yield chunk

    # Simple non-streaming version using safe_stream_chat:
    result = safe_stream_chat(request.prompt)
    return {"response": result["response"]}
```

**Run:**

```bash
uvicorn api:app --reload
```

**Test:**

```bash
curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{"prompt": "What is gradient descent?"}'
```

Notice what did not change: `gemini/` is untouched. The entire `gemini/` package
is provider-agnostic infrastructure. Only `api.py` is new — a different
interface layer consuming the same functions as `main.py`.

**What is `pydantic` and `BaseModel`?**

Pydantic is a data validation library that FastAPI uses. `BaseModel` is its
base class. When you define a class inheriting from `BaseModel` with type hints,
Pydantic automatically validates incoming JSON against those types and
raises descriptive errors for mismatches. `ChatRequest(**result)` unpacks a
dict into keyword arguments for the constructor.

---

## 18.5 Extension 4 — Persistent Conversation History

Currently, conversation history lives in a local variable in `demo_multi_turn()`
and disappears when the program exits. Persisting it across sessions requires storage.

**Simple file-based persistence:**

```python
import json
from pathlib import Path

HISTORY_FILE = Path("conversation_history.json")

def save_history(history: list) -> None:
    """Serialize history to JSON and save to disk."""
    serialized = [
        {
            "role": msg.role,
            "parts": [{"text": part.text} for part in msg.parts]
        }
        for msg in history
    ]
    HISTORY_FILE.write_text(json.dumps(serialized, ensure_ascii=False, indent=2))

def load_history() -> list:
    """Load history from disk and deserialize to types.Content objects."""
    from google.genai import types

    if not HISTORY_FILE.exists():
        return []

    data = json.loads(HISTORY_FILE.read_text())
    return [
        types.Content(
            role=msg["role"],
            parts=[types.Part(text=p["text"]) for p in msg["parts"]]
        )
        for msg in data
    ]
```

**What is `pathlib.Path`?**

`pathlib.Path` is Python's modern way to work with file paths. It is
cross-platform (works on Linux, macOS, and Windows) and offers clean methods:

```python
path = Path("conversation_history.json")
path.exists()           # → True if file exists
path.read_text()        # → file contents as string
path.write_text("...")  # → write string to file
```

**What is `json.dumps` / `json.loads`?**

`json.dumps(obj)` serializes a Python object to a JSON string.
`json.loads(string)` deserializes a JSON string back to a Python object.

```python
import json

data = {"name": "Nilton", "scores": [95, 87, 92]}

# Python → JSON string
json_str = json.dumps(data)
# '{"name": "Nilton", "scores": [95, 87, 92]}'

# JSON string → Python
restored = json.loads(json_str)
# {"name": "Nilton", "scores": [95, 87, 92]}
```

`ensure_ascii=False` allows non-ASCII characters (accented letters, emoji) in
the output. `indent=2` produces human-readable formatted JSON.

---

# Chapter 19: What to Study Next

## 19.1 Where This Project Leaves You

You now have hands-on experience with:

- Direct LLM API integration via an official SDK
- Python project modularization (packages, modules, imports)
- Multiple communication patterns (sync, streaming, multi-turn)
- Error handling architecture (exceptions, wrappers, result types)
- Software design principles (SRP, DRY, factory pattern, separation of concerns)
- Configuration and secrets management

This is a solid foundation. The next layer is knowing which directions to grow,
and in what order. Below are the most relevant paths for your specific context —
Data Science, MLOps, and AI application development.

---

## 19.2 Path 1 — Async Python

**What it is:** A programming model that allows a Python program to handle
multiple concurrent operations without threads or processes.

**Why it matters for LLM applications:** A web server handling many simultaneous
chat requests cannot afford to block one thread per request while waiting for
the API. Async lets one thread handle many requests concurrently.

**Core concepts to learn:**

```python
import asyncio

# async def defines a coroutine — a function that can be paused
async def fetch_response(prompt: str) -> str:
    # await pauses this coroutine until the result is ready
    # while paused, other coroutines can run
    response = await client.aio.models.generate_content(
        model=MODEL, contents=prompt, config=config
    )
    return response.text

# Run a coroutine
asyncio.run(fetch_response("hello"))
```

The Gemini SDK has async equivalents: `client.aio.models.generate_content()`
and `client.aio.models.generate_content_stream()`.

**Recommended resources:**
- Python docs: `asyncio` — HOWTO guide
- FastAPI docs: async endpoints
- `httpx` library: async HTTP client (replacement for `requests`)

**Estimated learning time:** 2–4 weeks for comfortable proficiency.

---

## 19.3 Path 2 — FastAPI for LLM APIs

**What it is:** A modern Python web framework for building REST APIs, with
automatic documentation and Pydantic validation.

**Why it matters:** Once you have an LLM client working, the next step is
making it accessible to other systems. FastAPI is the standard choice for
Python AI APIs.

**Key concepts to add to what you know:**

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str
    temperature: float = 0.3

class PromptResponse(BaseModel):
    success: bool
    response: str

@app.post("/chat", response_model=PromptResponse)
async def chat_endpoint(request: PromptRequest) -> PromptResponse:
    result = safe_chat(request.prompt)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["response"])
    return PromptResponse(success=True, response=result["response"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**What you already know that transfers:** Pydantic models are similar to
type-annotated dataclasses. `HTTPException` is a specialized exception with
a status code — the same HTTP status codes from Chapter 1.

**Recommended resources:**
- FastAPI official docs (excellent, with interactive examples)
- "FastAPI Tutorial" on the official site — do it sequentially

**Estimated learning time:** 1–2 weeks for basic proficiency.

---

## 19.4 Path 3 — LangChain and LangGraph

**What it is:** LangChain is a framework for building LLM applications with
higher-level abstractions: chains, agents, memory, and retrieval. LangGraph
extends it with stateful, graph-based agent workflows.

**Why it matters:** Direct SDK integration (what you built here) gives you
maximum control. LangChain gives you speed — pre-built patterns for RAG
(Retrieval-Augmented Generation), agents, and multi-step workflows.

**Key concepts:**

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# LangChain wraps the SDK
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=API_KEY,
    temperature=0.3
)

# Invoke the model
response = llm.invoke([
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="What is RAG?")
])
print(response.content)
```

**What you already know that transfers:**
- The concept of system prompts (same idea, different syntax)
- Multi-turn history (LangChain manages it, but same stateless underlying API)
- Streaming (LangChain supports `llm.stream()`)
- Error handling (LangChain raises its own exceptions)

The difference: your direct SDK code gives you full visibility and control.
LangChain hides much of this in exchange for powerful built-in patterns.
Knowing both makes you more versatile.

**Recommended resources:**
- LangChain Python docs: https://python.langchain.com
- LangGraph tutorials on the LangChain website

---

## 19.5 Path 4 — RAG (Retrieval-Augmented Generation)

**What it is:** A pattern where relevant documents are retrieved from a database
and injected into the prompt, giving the model access to knowledge beyond its
training data.

**Why it matters:** The most impactful real-world LLM applications (document
Q&A, internal knowledge bases, code search) are RAG applications.

**The components:**

```
User query
    │
    ▼
Embedding model → vector representation of query
    │
    ▼
Vector database (ChromaDB, Pinecone, FAISS)
→ finds documents most similar to query vector
    │
    ▼
Retrieved documents + original query → prompt
    │
    ▼
LLM → answer grounded in retrieved documents
```

**What you need to learn:**
- **Embeddings:** numerical vector representations of text
- **Vector similarity:** cosine similarity, dot product
- **Vector databases:** ChromaDB (local), Pinecone (cloud), pgvector (Postgres)
- **Chunking strategies:** how to split documents for retrieval
- **Prompt construction:** how to inject retrieved context cleanly

**What you already know that transfers:**
- Multi-turn history management (retrieved context is just more content in the prompt)
- System prompts (RAG typically uses a system prompt that says "answer only based on the provided context")
- Token limits (retrieved context consumes tokens — you must budget carefully)

**Recommended starting point:**
Build a local RAG system with ChromaDB and the Gemini SDK. No LangChain yet —
understand the components directly first.

---

## 19.6 Path 5 — MLOps: Versioning, Tracking, Deployment

**What it is:** The practices and tools for running ML systems reliably in
production — model versioning, experiment tracking, deployment pipelines,
monitoring.

**Why it matters:** You already have MLflow experience. The patterns from
classical ML (track experiments, version models, monitor drift) apply to
LLM applications too, with some additions:

| Classical ML | LLM equivalent |
|---|---|
| Hyperparameter tuning | Prompt engineering, temperature tuning |
| Model versioning | Prompt versioning |
| Inference latency | Token generation latency, TTFT (time to first token) |
| Prediction drift | Response quality drift |
| A/B testing models | A/B testing prompts or providers |

**LLM-specific MLOps tools:**
- **LangSmith:** tracing and evaluation for LangChain apps
- **Weights & Biases:** experiment tracking with LLM support
- **Promptflow (Microsoft):** prompt engineering and evaluation workflows

**What you already know that transfers:** Everything from your existing MLflow
work. The concepts are the same; the subject being tracked shifts from model
weights to prompts and generation parameters.

---

## 19.7 Path 6 — Containerization and Deployment

**What it is:** Packaging your application and its dependencies into a Docker
container so it runs identically in any environment.

**Why it matters:** The path from "works on my machine" to "runs in production"
goes through Docker. For LLM applications, containerization also makes it
easy to deploy to cloud services (Cloud Run, AWS Lambda, GCP).

**Minimal Dockerfile for this project:**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Never bake secrets into images — pass as environment variables
ENV GEMINI_API_KEY=""

CMD ["python", "main.py"]
```

**Build and run:**

```bash
docker build -t llm-api-client .
docker run -e GEMINI_API_KEY="AIzaSy-..." llm-api-client
```

**Notice the secret handling:** The API key is not in the Dockerfile or in
any committed file — it is passed as an environment variable at runtime (`-e`).
This is the production pattern from Chapter 3, now applied correctly.

**What you already know that transfers:**
- Environment variables for secrets (Chapter 3)
- `requirements.txt` (already in the project)
- The `if __name__ == "__main__"` entry point is exactly what `CMD` runs

**Recommended resources:**
- Docker's official "Get Started" tutorial
- Your existing MLOps Zoomcamp — it likely covers Docker in depth

---

## 19.8 A Suggested Learning Sequence

Given your background (Data Science, ML experience, Python proficiency,
MLflow familiarity), here is a practical sequence:

**Weeks 1–2: Consolidate this project**
- Run all three demos until they feel natural
- Rewrite `gemini/operations.py` from memory without looking
- Extend the project with one of the extensions from Chapter 18

**Weeks 3–4: FastAPI**
- Build a REST API wrapper around the `gemini/` package
- Add a `/chat` endpoint (synchronous) and a `/health` endpoint
- Deploy it locally with `uvicorn`

**Weeks 5–6: Async Python**
- Convert `simple_chat()` to `async def async_simple_chat()`
- Convert the FastAPI endpoint to `async def`
- Understand the event loop — run multiple prompts concurrently

**Weeks 7–8: RAG from scratch**
- Build a document Q&A system: ingest a PDF, chunk it, embed it, store in ChromaDB
- Retrieve relevant chunks for each query
- Inject into the prompt and compare with/without RAG

**Weeks 9–10: LangChain/LangGraph**
- Rebuild your RAG system in LangChain
- Understand what the framework added and what it hid
- Explore agents: a simple tool-using agent that can call two or three functions

**Ongoing:**
- Add MLflow tracking to your LLM experiments (log prompts, parameters, responses)
- Containerize everything
- Follow the MLOps Zoomcamp modules relevant to deployment

---

## 19.9 Interview Preparation: What You Can Now Defend

Based on the work done in this project, here are the specific claims you can
make in technical interviews — and what you need to be ready to explain for each:

**"I've integrated LLM APIs directly via official Python SDKs."**
- The difference between the old (`google.generativeai`) and new (`google-genai`) SDK
- Why `genai.Client(api_key=)` is better than `genai.configure()`
- What the `x-goog-api-key` header contains and when it is sent
- What happens on a 403 vs. a 429

**"I understand streaming and how it works at the protocol level."**
- Server-Sent Events: persistent connection, chunks over time
- The difference between synchronous and streaming responses
- `flush=True` and why buffering matters for real-time output
- Callbacks as a pattern for decoupling token delivery from display

**"I've designed a modular Python project with clean separation of concerns."**
- Which file has which responsibility in this project
- Why `main.py` has zero API logic
- What `__init__.py` does and why it exists
- The difference between absolute and relative imports

**"I handle API errors gracefully with structured responses."**
- The `ClientError`/`ServerError` hierarchy
- Why 4xx and 5xx require different responses
- The Result dict pattern and why it keeps `main.py` clean
- Exponential backoff for rate limit errors

**"I've implemented multi-turn conversations with a stateless API."**
- What stateless means and why it requires resending history
- The `types.Content` structure: role and parts
- Why `role="model"` in Gemini vs. `role="assistant"` elsewhere
- The shallow copy pattern and why it protects history on failure

---

## 19.10 Final Reflection: What This Project Actually Taught

This project is small — under 400 lines of actual code across seven files.
But the concepts it embodies are not small:

**From software engineering:**
Single Responsibility, DRY, factory patterns, abstraction boundaries, dependency
direction, public vs. private interfaces. These principles appear in every
serious Python codebase. You have seen them applied to a real problem, not
described abstractly.

**From API design:**
HTTP methods, status codes, request-response cycles, authentication, rate
limits, REST statelessness. These are not Gemini-specific — they describe
how every REST API works. Every provider you work with will use the same vocabulary.

**From Python:**
Type hints, packages, `__init__.py`, relative imports, `**kwargs`, dispatch
tables, iterators, `if __name__ == "__main__"`. These are the intermediate
Python concepts that separate "someone who can write scripts" from "someone
who can build systems."

**From LLM application development:**
Tokens, context windows, temperature, system prompts, streaming, multi-turn
context — the concepts that govern how language models actually behave in
production, not just in demo notebooks.

The measure of whether you have actually learned something is whether you
can build it again from scratch. Put this book down. Create a new empty
directory. Write the project from memory. Look things up when you are stuck,
but write the code yourself. The second time will be faster. The third time,
it will feel obvious.

That is when you own it.

---

## Part 6 Summary

| Topic | What you can now do |
|---|---|
| Project reading | Trace any line of code to its origin and explain its purpose |
| Adding providers | Mirror the `gemini/` structure for any other SDK |
| Function calling | Extend `operations.py` with tool-use support |
| FastAPI | Expose the `gemini/` package as a REST API |
| Persistence | Serialize/deserialize history to JSON for cross-session memory |
| Async Python | Understand the concept and where to go to learn it |
| RAG | Know the components (embed, store, retrieve, inject) |
| MLOps for LLMs | Map classical ML tracking concepts to prompt/parameter tracking |
| Docker | Know how to containerize with secrets passed at runtime |
| Interview defense | Articulate every design decision in this project |

---

## Complete Book Summary

**Part 1 — Foundations**
Tokens, HTTP, JSON, REST, SDKs, Python modules and packages, separation of
concerns, configuration management, secrets handling, type hints.

**Part 2 — The Gemini SDK**
Authentication (API key, headers, 403), `genai.Client`, factory functions,
generation parameters (model, temperature, max_tokens, system prompt),
`**kwargs` and `.get()`, response object structure, token accounting.

**Part 3 — Communication Patterns**
Synchronous calls and blocking, request-response lifecycle, streaming and SSE,
iterators, `flush=True`, callbacks, stateless APIs, `types.Content` and roles,
list mutation, tuple returns, shallow vs. deep copy, token cost growth.

**Part 4 — Writing Robust Code**
Exception hierarchy, tracebacks, `try/except`, `isinstance()`, string inspection
for status codes, exponential backoff, the safe wrapper pattern, Result dicts,
`_handle_error()`, Single Responsibility, DRY, factory pattern, dependency
direction, `__all__` and naming conventions.

**Part 5 — Python Concepts**
Type hints (basic, container, union, `Callable`), dicts (operations, Result
pattern, dispatch tables), first-class functions, `*args`/`**kwargs`,
`__init__.py` mechanics, `__all__`, absolute vs. relative imports, `sys.modules`
cascade, `__name__`, `if __name__ == "__main__"`, dunder names, module-level code.

**Part 6 — Putting It All Together**
Full project walkthrough in dependency order, four extension patterns (providers,
function calling, FastAPI, persistence), six learning paths (async, FastAPI,
LangChain, RAG, MLOps, Docker), interview talking points, suggested learning
sequence.

---

*End of "Building LLM API Clients in Python — A Hands-on Guide"*

