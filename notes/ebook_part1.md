# Building LLM API Clients in Python — A Hands-on Guide

## Part 1 — Foundations

> Chapters 1, 2, and 3
> Prerequisites: basic Python familiarity, general programming background

---

# Chapter 1: How LLMs and APIs Work

## 1.1 What is a Large Language Model?

A Large Language Model (LLM) is a neural network trained on massive amounts of text. During training, it learns statistical patterns between words, sentences, and ideas — well enough to generate coherent, contextually relevant text when given a prompt.

You do not need to understand the full mathematics of neural networks to work with LLMs via an API. What you need is a mental model of the input-output contract:

```
Input  (prompt)  →  [LLM]  →  Output (completion)
```

You send text in. The model returns text out. Everything else — weights, attention heads, transformer layers — is abstracted away by the API provider.

---

## 1.2 What is a Token?

Before text enters the model, it is split into **tokens** — the fundamental unit of processing and billing.

A tokenizer breaks sentences into pieces that may be whole words, partial words, punctuation, or spaces. The exact boundaries depend on the tokenizer used, but a useful approximation for English is:

```
1 token ≈ 4 characters ≈ ¾ of a word
```

Examples:

| Text | Approximate token count |
|---|---|
| `"Hello"` | 1 |
| `"Hello, world!"` | 4 |
| `"What is backpropagation?"` | 5 |
| A short paragraph (100 words) | ~130 tokens |
| This entire chapter | ~3,000–4,000 tokens |

**Why tokens matter:**

1. **Billing.** API providers charge per token — input tokens (your prompt) and output tokens (the model's response) are counted separately.

2. **Context window.** Every model has a maximum number of tokens it can process at once (input + output combined). Exceed it and the request fails. Gemini 2.5 Flash, for example, supports up to 1,048,576 input tokens.

3. **`max_output_tokens`.** The parameter you set in `config.py` is a hard ceiling on how many output tokens the model can generate. If the model hasn't finished when it hits this limit, it stops mid-sentence. Only tokens actually generated are billed — setting a high ceiling doesn't cost more if the model finishes early.

---

## 1.3 What is an API?

**API** stands for Application Programming Interface. It is a defined contract that lets two programs communicate, regardless of what language they are written in or where they run.

When you call the Gemini API:

1. Your Python script constructs an **HTTP request** — a structured message sent over the internet.
2. Google's servers receive it, pass your prompt to the model, and generate a response.
3. The response travels back to your script as an **HTTP response**.

This is functionally identical to what your browser does when it loads a web page — just with structured data instead of HTML.

---

## 1.4 HTTP: The Language of the Web

HTTP (HyperText Transfer Protocol) defines how messages are formatted and transmitted between clients (your script) and servers (Google's API).

Every HTTP interaction has two parts:

**Request** — sent by the client:
```
Method : POST
URL    : https://api.google.com/v1/models/gemini-2.5-flash:generateContent
Headers: Content-Type: application/json
         x-goog-api-key: AIzaSy...
Body   : { "contents": [...], "generationConfig": {...} }
```

**Response** — sent by the server:
```
Status : 200 OK
Headers: Content-Type: application/json
Body   : { "candidates": [...], "usageMetadata": {...} }
```

The most important HTTP concepts for API work:

### HTTP Methods

| Method | Meaning | Used for |
|---|---|---|
| `GET` | Retrieve data | Listing models, fetching resources |
| `POST` | Send data, trigger action | Generating content, creating resources |
| `PUT` | Replace a resource | Updating configurations |
| `DELETE` | Remove a resource | Deleting resources |

The Gemini `generateContent` endpoint uses **POST** because you are sending a prompt and triggering a computation — not merely retrieving stored data.

### HTTP Status Codes

Status codes tell you whether a request succeeded or failed. They are grouped by their first digit:

| Range | Category | Common examples |
|---|---|---|
| 2xx | Success | 200 OK, 201 Created |
| 4xx | Client error (your fault) | 400 Bad Request, 403 Forbidden, 404 Not Found, 429 Too Many Requests |
| 5xx | Server error (their fault) | 500 Internal Server Error, 503 Service Unavailable |

You have already encountered these in the project:
- `403` → wrong API key (`PERMISSION_DENIED`)
- `404` → model name not found (`NOT_FOUND`)
- `429` → too many requests (`RESOURCE_EXHAUSTED`)

### HTTP Headers

Headers are key-value metadata attached to both requests and responses. The SDK sends these automatically, but it helps to know what they are:

```
x-goog-api-key: AIzaSy...        ← your authentication token
Content-Type: application/json   ← tells the server the body is JSON
```

---

## 1.5 JSON: The Data Format

**JSON** (JavaScript Object Notation) is the standard format for exchanging data in APIs. Despite the name, it is language-agnostic and used everywhere.

JSON looks like Python dictionaries and lists — because Python's `dict` and `list` were largely inspired by it:

```json
{
  "model": "models/gemini-2.5-flash",
  "contents": [
    {
      "role": "user",
      "parts": [{ "text": "What is a transformer?" }]
    }
  ],
  "generationConfig": {
    "temperature": 0.3,
    "maxOutputTokens": 2048
  }
}
```

The SDK serializes your Python objects into JSON before sending the request, and deserializes the JSON response back into Python objects. You never write raw JSON in this project — the SDK handles it. But knowing the format helps when reading API documentation or debugging raw HTTP logs.

---

## 1.6 REST APIs

The Gemini API is a **REST API** (Representational State Transfer). REST is an architectural style — a set of conventions for designing APIs that are predictable and easy to use.

Key REST conventions relevant to this project:

**Resources and URLs:**
Each URL represents a resource or action. The Gemini endpoint pattern is:
```
POST /v1/{model}:generateContent
```
`v1` is the API version. Versioned URLs mean Google can release `v2` with breaking changes without breaking your existing code.

**Statelessness:**
This is the most important REST property for our project. Each HTTP request must be completely self-contained. The server stores no session state between calls. If you want the model to "remember" the previous turn, you must include it in the current request.

This is exactly why `multi_turn_chat()` in `operations.py` resends the full history every time:

```python
# Turn 3 must include turns 1 and 2, otherwise the model has no context
response = client.models.generate_content(
    model=MODEL,
    contents=history,   # full conversation history
    config=config,
)
```

---

## 1.7 SDKs: Why We Don't Write Raw HTTP

An **SDK** (Software Development Kit) is a library provided by the API vendor that wraps the raw HTTP calls in idiomatic code for your language.

Without the SDK, a Gemini request in Python would look like:

```python
import requests
import json

url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
headers = {
    "Content-Type": "application/json",
    "x-goog-api-key": API_KEY,
}
body = {
    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
    "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048},
}
response = requests.post(url, headers=headers, json=body)
data = response.json()
text = data["candidates"][0]["content"]["parts"][0]["text"]
```

With the SDK:

```python
from google import genai

client = genai.Client(api_key=API_KEY)
response = client.models.generate_content(model=MODEL, contents=prompt, config=config)
text = response.text
```

The SDK handles:
- Constructing the correct URL and headers
- Serializing your arguments to JSON
- Deserializing the response
- Raising typed exceptions on errors
- Retrying transient failures

The tradeoff is abstraction: the SDK hides details you sometimes need to understand for debugging. Knowing the raw HTTP layer (as covered in this chapter) makes you a better SDK user.

---

# Chapter 2: Python Project Structure and Modules

## 2.1 What is a Module?

In Python, any `.py` file is a **module**. A module is a reusable unit of code with a namespace — its own isolated collection of variables, functions, and classes.

```
config.py       ← a module
main.py         ← a module
gemini/client.py ← a module inside a package
```

When you write `from config import API_KEY`, Python executes `config.py` (if it hasn't already), and makes the name `API_KEY` available in the current file's namespace.

---

## 2.2 What is a Package?

A **package** is a directory of modules, identified by the presence of an `__init__.py` file.

```
gemini/               ← this is a package
├── __init__.py       ← this file makes it a package
├── client.py         ← module
├── operations.py     ← module
└── errors.py         ← module
```

Without `__init__.py`, Python would not recognize `gemini/` as a package and `from gemini import ...` would fail.

The `__init__.py` file serves two purposes:
1. Marks the directory as a package.
2. Runs when the package is first imported — commonly used to re-export names from sub-modules.

---

## 2.3 Import Styles

Python has several ways to import:

```python
# Import the whole module — access names with dot notation
import config
key = config.API_KEY

# Import specific names — bring them into the current namespace
from config import API_KEY
key = API_KEY

# Import with an alias — useful for long names
import google.generativeai as genai

# Relative import — only valid inside a package
# The dot means "same package"
from .client import create_client       # gemini/errors.py importing from gemini/client.py
from ..config import API_KEY            # two dots = parent package
```

In this project, `gemini/errors.py` uses relative imports:

```python
from .operations import simple_chat, stream_chat, multi_turn_chat
```

The leading `.` means "look in the same package (`gemini/`)." This is preferred inside packages because it works regardless of where the package is installed.

---

## 2.4 Separation of Concerns

**Separation of Concerns** (SoC) is a design principle that says each component of a system should handle one distinct aspect of the problem and be ignorant of the others.

In our project:

```
config.py          → WHAT values to use (keys, model, parameters)
gemini/client.py   → HOW to authenticate and configure the SDK
gemini/operations.py → HOW to call the API (the actual requests)
gemini/errors.py   → WHAT to do when something goes wrong
main.py            → HOW to present results to the user
```

Each file can be changed independently. If Google changes authentication, you update `client.py`. If you want different error messages, you update `errors.py`. Neither change touches the other files.

The practical benefit becomes clear when you compare the flat version (one big `api_client.py`) to the modular version:

| Flat version | Modular version |
|---|---|
| One file does everything | Each file does one thing |
| Hard to test parts in isolation | Each module is independently testable |
| Growing file becomes harder to navigate | Each file stays small and focused |
| One change can accidentally break unrelated code | Changes are contained to their module |

---

## 2.5 The Project File Tree Explained

```
llm-api-client/
│
├── config.py          ← reads my_api_keys.py, defines all tunable parameters
├── main.py            ← entry point; imports from gemini/, no API logic
├── list_models.py     ← standalone utility; depends only on config.py
├── my_api_keys.py     ← secret store; git-ignored
├── requirements.txt   ← dependency list for pip/pipenv
├── README.md          ← project documentation
│
└── gemini/            ← the Gemini API package
    ├── __init__.py    ← re-exports public functions; defines __all__
    ├── client.py      ← create_client(), create_config()
    ├── operations.py  ← simple_chat(), stream_chat(), multi_turn_chat()
    └── errors.py      ← _handle_error(), safe_chat(), safe_stream_chat(),
                          safe_multi_turn_chat()
```

**Dependency flow** — each file only imports from files below it in the chain:

```
main.py
  └── imports from gemini/ (via __init__.py)
        └── errors.py imports from operations.py
              └── operations.py imports from client.py
                    └── client.py imports from config.py
                          └── config.py imports from my_api_keys.py
```

No circular dependencies. Each layer knows about the layer below — never above. This is called a **directed acyclic dependency graph** and it is the foundation of maintainable software.

---

## 2.6 Why Not Put Everything in One File?

For a small script, one file is fine. The modular structure becomes valuable when:

- **You add a second provider** (e.g., Anthropic). You create an `anthropic/` package alongside `gemini/` with the same public interface. `main.py` doesn't change at all.
- **You want to test operations without errors.** You can import `gemini.operations` directly and get raw exceptions — useful in test scripts.
- **Someone else reads your code.** Each file's purpose is immediately clear from its name and location.
- **You add new features.** A new streaming mode goes in `operations.py`. A new error type goes in `errors.py`. You never have to search a 500-line file.

---

# Chapter 3: Configuration and Secrets Management

## 3.1 What is Configuration?

**Configuration** is the set of values that control how software behaves without changing its logic. In this project:

- Which model to use → `MODEL`
- How creative responses should be → `TEMPERATURE`
- How long responses can be → `MAX_TOKENS`
- What role the AI plays → `SYSTEM_PROMPT`
- Which account to authenticate as → `API_KEY`

All of these live in `config.py`. The functions in `operations.py` use them but don't define them — and don't need to know where they came from.

---

## 3.2 Why Separate Configuration from Logic?

Consider the alternative: hardcoding values directly in functions.

```python
# Hardcoded — bad
def simple_chat(prompt):
    client = genai.Client(api_key="AIzaSy...")
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=prompt,
        config=GenerateContentConfig(temperature=0.3, max_output_tokens=2048)
    )
    return response.text
```

Problems:
- To change the model, you have to find and edit every function that uses it.
- The API key is buried in business logic.
- You cannot change behavior without changing code.

With a central `config.py`:

```python
# config.py — one place to change
MODEL = "models/gemini-2.5-flash"
TEMPERATURE = 0.3
MAX_TOKENS = 2048

# operations.py — never needs to change for configuration
def simple_chat(prompt):
    client = create_client()          # reads API_KEY from config
    config = create_config()          # reads TEMPERATURE, MAX_TOKENS from config
    return client.models.generate_content(model=MODEL, ...).text
```

---

## 3.3 Secrets: What They Are and Why They're Dangerous

A **secret** is any value that grants access to a resource and must be kept confidential:
- API keys
- Database passwords
- OAuth tokens
- Private certificates

In this project, the secret is `MY_GOOGLE_API_KEY` in `my_api_keys.py`.

**Why are exposed secrets dangerous?**

If your API key is committed to a public GitHub repository, automated bots scan for it within seconds. They use it to make requests — billed to your account. This has cost developers thousands of dollars overnight.

---

## 3.4 The my_api_keys.py Pattern

The pattern used in this project:

```
my_api_keys.py     ← actual secret lives here
config.py          ← imports from my_api_keys.py
.gitignore         ← my_api_keys.py listed here → never committed
```

`my_api_keys.py`:
```python
MY_GOOGLE_API_KEY = "AIzaSy-YOUR-KEY-HERE"
```

`config.py`:
```python
from my_api_keys import MY_GOOGLE_API_KEY
API_KEY: str = MY_GOOGLE_API_KEY
```

`.gitignore`:
```
my_api_keys.py
```

The `.gitignore` file tells Git to never track `my_api_keys.py`. Even if you run `git add .`, the secrets file is excluded. The rest of the codebase can be public without risk.

**Setting up `.gitignore`:**
```bash
echo "my_api_keys.py" >> .gitignore
git rm --cached my_api_keys.py   # removes it from tracking if already committed
```

---

## 3.5 The Production Pattern: Environment Variables

For production code or shared repositories, secrets should come from **environment variables** — values stored in the operating system's process environment, outside the codebase entirely.

Setting an environment variable in Linux/macOS:
```bash
export GEMINI_API_KEY="AIzaSy-YOUR-KEY-HERE"
```

Reading it in Python:
```python
import os
API_KEY = os.environ.get("GEMINI_API_KEY")
```

`os.environ` is a dictionary-like object that holds all environment variables for the current process. `.get("KEY")` returns the value if it exists, or `None` if it doesn't (safer than `os.environ["KEY"]`, which raises `KeyError` if missing).

**Environment variables vs. the `my_api_keys.py` pattern:**

| Approach | Good for | Risk |
|---|---|---|
| `my_api_keys.py` + `.gitignore` | Local development, learning | Accidentally committed if `.gitignore` is wrong |
| Environment variables | Production, CI/CD pipelines | Must be set on every machine that runs the code |
| Secrets manager (AWS, GCP) | Team environments, cloud deployment | More setup, highest security |

For a learning project running locally, `my_api_keys.py` is perfectly appropriate. When you move to deploying an application, switch to environment variables.

---

## 3.6 Type Hints in config.py

Throughout `config.py`, you see annotations like:

```python
API_KEY: str = MY_GOOGLE_API_KEY
MODEL: str = "models/gemini-2.5-flash"
MAX_TOKENS: int = 2048
TEMPERATURE: float = 0.3
```

The `: str`, `: int`, `: float` are **type hints** (also called type annotations). They are documentation for humans and tools — Python does not enforce them at runtime.

```python
MAX_TOKENS: int = 2048
MAX_TOKENS = "hello"   # Python allows this at runtime — no error
```

However, tools like `mypy` (a static type checker) and editors like VS Code will flag the second line as incorrect. This catches bugs before they run.

The three most common basic types:
- `str` — text string: `"hello"`, `"models/gemini-2.5-flash"`
- `int` — integer number: `2048`, `0`, `-1`
- `float` — decimal number: `0.3`, `1.0`, `2.0`

For function return types, the annotation goes after `->`:
```python
def simple_chat(prompt: str) -> str:   # takes a str, returns a str
    ...

def header(title: str) -> None:        # takes a str, returns nothing
    ...
```

`None` here means the function has no return value (it only produces side effects like printing).

---

## 3.7 The `.strip()` Method on Strings

In `config.py`, the system prompt ends with:

```python
SYSTEM_PROMPT: str = """
You are a friendly technical assistant...
""".strip()
```

**What is `.strip()?`**

String methods are functions that belong to string objects and are called with dot notation. `.strip()` removes all leading and trailing whitespace characters — spaces, tabs, and newlines (`\n`).

The triple-quoted string (`"""..."""`) starts with a newline right after the opening quotes:

```python
s = """
Hello
"""
# s = "\nHello\n"   ← has newlines at start and end

s.strip()
# = "Hello"         ← clean
```

Without `.strip()`, the system prompt would begin with a newline, which adds unnecessary whitespace before your instruction when the SDK sends it to the model. It is a small but clean habit.

---

## Part 1 Summary

You now have a foundation for everything that follows. Let's consolidate the key ideas:

| Concept | One-line summary |
|---|---|
| Token | The unit of text processing and billing in LLMs (~4 chars) |
| HTTP | The protocol that moves data between your script and the API server |
| Status code | A number indicating success (2xx) or failure (4xx/5xx) |
| REST | An API design style; key property: statelessness |
| SDK | A library that wraps raw HTTP in idiomatic language code |
| Module | Any `.py` file; a reusable, namespaced unit of code |
| Package | A directory of modules identified by `__init__.py` |
| Separation of Concerns | Each file handles one aspect of the system |
| Configuration | Values that control behavior without changing logic |
| Secret | A value that grants access and must never be public |
| Type hint | Annotation documenting expected types (not enforced at runtime) |
| `.strip()` | String method that removes leading/trailing whitespace |

---

*Next: Part 2 — The Gemini SDK (Chapters 4, 5, and 6)*
*Authentication, generation parameters, and making your first API call in detail.*

