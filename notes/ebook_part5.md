# Building LLM API Clients in Python — A Hands-on Guide

## Part 5 — Python Concepts Used in This Project

> Chapters 13, 14, 15, and 16
> Covers: type hints, dictionaries and dispatch tables, packages and relative imports,
> and the if __name__ == "__main__" pattern

---

# Chapter 13: Type Hints and Return Annotations

## 13.1 What are Type Hints?

Python is a **dynamically typed** language. This means types are checked at runtime,
not at compile time, and you can assign any value to any variable at any point:

```python
x = 42        # x is an int
x = "hello"   # x is now a str — Python allows this
x = [1, 2, 3] # x is now a list — still allowed
```

**Type hints** (also called type annotations) are an opt-in layer of documentation
that lets you declare what types variables, parameters, and return values are
*expected* to be:

```python
def simple_chat(prompt: str) -> str:
    ...
```

The `: str` after `prompt` says "this parameter expects a string."
The `-> str` after the closing parenthesis says "this function returns a string."

**Critical point: Python does not enforce type hints at runtime.**

```python
def simple_chat(prompt: str) -> str:
    return 42   # Python runs this without error

result = simple_chat(99)   # also runs without error
```

Type hints are read by:
- **Humans** — they communicate intent and make code easier to understand
- **Editors** — VS Code, PyCharm use them to power autocomplete and inline docs
- **Type checkers** — tools like `mypy` analyze your code statically and flag violations
- **Documentation generators** — tools like Sphinx can extract type information

The value is not in runtime enforcement but in catching mistakes *before* running,
through static analysis.

---

## 13.2 Basic Type Hint Syntax

**Variable annotations:**

```python
API_KEY: str = "AIzaSy-..."
MAX_TOKENS: int = 2048
TEMPERATURE: float = 0.3
IS_STREAMING: bool = False
```

**Function parameter annotations:**

```python
def greet(name: str, times: int) -> str:
    return (name + " ") * times
```

**The four primitive types:**

| Type | Python name | Example values |
|---|---|---|
| Text | `str` | `"hello"`, `"models/gemini-2.5-flash"` |
| Integer | `int` | `0`, `2048`, `-1` |
| Decimal | `float` | `0.3`, `1.0`, `3.14` |
| Boolean | `bool` | `True`, `False` |

---

## 13.3 Container Type Hints

For collections, type hints can describe what the collection contains:

```python
from typing import Optional   # needed for Python < 3.10

# A list of strings
def process_prompts(prompts: list[str]) -> list[str]:
    return [p.strip() for p in prompts]

# A dictionary mapping strings to integers
word_counts: dict[str, int] = {"hello": 3, "world": 1}

# A tuple of specific types (str first, list second)
def multi_turn_chat(history: list, new_message: str) -> tuple[str, list]:
    ...

# Optional: either the type or None
def find_model(name: str) -> str | None:   # Python 3.10+
    ...
# Equivalent in older Python:
# from typing import Optional
# def find_model(name: str) -> Optional[str]:
```

**`tuple[str, list]` as a return type:**

In `multi_turn_chat()`, the return type `tuple[str, list]` precisely documents
that the function returns two values: first a string, then a list. This is how
Python declares multi-value returns.

---

## 13.4 None as a Type

`None` is Python's null value — it represents "no value" or "nothing."

As a type hint, `None` means "this function returns nothing":

```python
def header(title: str) -> None:   # does not return a value
    print(f"\n{'=' * 60}\n  {title}\n{'=' * 60}")
```

Functions without a `return` statement implicitly return `None`. Annotating
`-> None` makes this explicit and signals to readers: "do not use the return
value of this function."

**`None` as a parameter default:**

```python
def stream_chat(prompt: str, callback=None) -> str:
```

`callback=None` means the parameter is optional — if the caller does not pass it,
it defaults to `None`. Inside the function, `if callback:` is `False` when
`callback` is `None` (because `None` is falsy), and `True` when a function
was passed.

**`str | None` — the union type:**

```python
def safe_chat(prompt: str) -> dict:
    return {
        "success": True,
        "response": "...",
        "error_type": None   # ← None here
    }
```

In the result dict, `"error_type"` is either `None` (success) or a string
(failure). The full type of this value would be written `str | None`,
meaning "either a str or None." This is called a **union type**.

---

## 13.5 Type Hints for Callable (Function) Types

When a parameter is itself a function (like `callback`), the most precise
annotation uses `Callable`:

```python
from typing import Callable

def stream_chat(
    prompt: str,
    callback: Callable[[str], None] | None = None
) -> str:
```

`Callable[[str], None]` reads as: "a callable that accepts one `str` argument
and returns `None`."

In this project, we wrote `callback=None` without the full `Callable` annotation
for readability. Both approaches are valid — the simpler form is more common in
projects that use type hints for documentation rather than strict checking.

---

## 13.6 Return Type Annotations in This Project

Every function in the project has an explicit return annotation. Let's collect
them and examine what each communicates:

```python
# gemini/client.py
def create_client() -> genai.Client:
    # returns a genai.Client object

def create_config(**overrides) -> types.GenerateContentConfig:
    # returns a GenerateContentConfig object

# gemini/operations.py
def simple_chat(prompt: str) -> str:
    # returns the response text

def stream_chat(prompt: str, callback=None) -> str:
    # returns the accumulated text (even though it also prints/calls callback)

def multi_turn_chat(history: list, new_message: str) -> tuple[str, list]:
    # returns (response_text, updated_history)

# gemini/errors.py
def _handle_error(error: Exception) -> dict:
    # returns {"success": False, "response": ..., "error_type": ...}

def safe_chat(prompt: str) -> dict:
    # returns {"success": bool, "response": str, "error_type": str|None}

def safe_multi_turn_chat(history: list, new_message: str) -> dict:
    # returns {"success": bool, "response": str, "history": list, "error_type": str|None}

# main.py
def header(title: str) -> None:   # side effect only
def footer(info: str = "") -> None:   # side effect only
def demo_simple_chat() -> None:   # runs interactive loop, no return value
def demo_streaming() -> None:
def demo_multi_turn() -> None:
```

The pattern is consistent: functions that compute and return data have specific
return types; functions that produce side effects (printing, running loops)
return `None`.

---

## 13.7 When to Use Type Hints

**Always:**
- Public functions (those called from outside the module)
- Function parameters and return types in any code others will read
- Module-level constants (`API_KEY: str = ...`)

**Usually:**
- Internal helper functions (like `_handle_error`)
- Variables whose type is not immediately obvious from the value

**Optionally:**
- Variables where the type is trivially obvious: `count = 0` (clearly an int),
  `name = "Alice"` (clearly a str)

In a learning context, annotating everything is valuable — it forces you to think
explicitly about what types each function works with.

---

# Chapter 14: Dictionaries, Dispatch Tables, and **kwargs

## 14.1 Dictionaries: Python's Most Versatile Data Structure

A **dictionary** (`dict`) is a collection of key-value pairs. Keys must be unique
and hashable (strings and numbers are hashable; lists are not). Values can be
anything.

```python
# Creating a dict
person = {
    "name": "Nilton",
    "role": "Senior Data Analyst",
    "skills": ["Python", "SQL", "Power BI"]
}

# Accessing values
person["name"]          # → "Nilton"
person.get("age", 0)    # → 0 (key missing, returns default)

# Adding or updating a key
person["location"] = "Rio de Janeiro"

# Checking if a key exists
"name" in person        # → True
"salary" in person      # → False

# Iterating
for key, value in person.items():
    print(f"{key}: {value}")

# Getting all keys or values
person.keys()    # → dict_keys(["name", "role", "skills", "location"])
person.values()  # → dict_values(["Nilton", "Senior Data Analyst", ...])
```

---

## 14.2 The Result Dict Pattern Revisited

Throughout `errors.py`, we return dicts as structured results:

```python
return {
    "success": True,
    "response": response_text,
    "error_type": None
}
```

This is a **heterogeneous dict** — a dict where values have different types
(`bool`, `str`, `None`). Dicts used this way are essentially a lightweight
alternative to defining a class or using a `dataclass`.

The tradeoff:

```python
# Dict approach — flexible, no class needed
result = safe_chat("hello")
result["success"]    # works
result["succcess"]   # typo — KeyError at runtime, no warning beforehand

# Dataclass approach — structured, editor can catch typos
from dataclasses import dataclass

@dataclass
class ChatResult:
    success: bool
    response: str
    error_type: str | None = None

result = safe_chat("hello")
result.success    # works
result.succcess   # AttributeError — and editor highlights the typo
```

For a learning project, the dict approach is simpler. In production code with
many consumers of the result, a `dataclass` or `TypedDict` would be preferable.

---

## 14.3 Dispatch Tables: Functions as Values

In `main.py`:

```python
demos = {
    "1": demo_simple_chat,
    "2": demo_streaming,
    "3": demo_multi_turn,
}

if choice in demos:
    demos[choice]()
```

This is a **dispatch table** — a dictionary that maps keys to callable functions.
It replaces what would otherwise be an `if/elif` chain:

```python
# Without dispatch table
if choice == "1":
    demo_simple_chat()
elif choice == "2":
    demo_streaming()
elif choice == "3":
    demo_multi_turn()
else:
    print("Invalid choice")
```

Both work. The dispatch table approach has several advantages:

**Extensibility:** Adding a new demo means one line in the dict and one
`print()` in the menu. With `if/elif`, you must add another `elif` and remember
to keep them in sync.

**Functions as first-class values:** This pattern only works because Python
treats functions as **first-class objects** — they can be stored in variables,
passed as arguments, stored in data structures, and returned from other functions.

```python
def greet():
    print("hello")

# greet is a function object
type(greet)        # → <class 'function'>

# Store it in a variable
fn = greet
fn()               # → prints "hello"

# Store it in a dict
actions = {"greet": greet}
actions["greet"]() # → prints "hello"
```

`demo_simple_chat` (no parentheses) is the function object.
`demo_simple_chat()` (with parentheses) calls it immediately.

When we write `"1": demo_simple_chat` in the dict, we store the function object.
When we write `demos[choice]()`, we retrieve the function object and then call it.

**O(1) lookup:** Dict lookup is constant time — it takes the same amount of time
regardless of how many entries exist. An `if/elif` chain is O(n) — it checks
conditions one by one until it finds a match. For three options this is
imperceptible; for fifty options, the dict is measurably faster.

---

## 14.4 Dictionaries for Configuration

`config.py` uses module-level variables rather than a dict for configuration:

```python
MODEL: str = "models/gemini-2.5-flash"
TEMPERATURE: float = 0.3
```

An alternative approach many projects use is a configuration dict:

```python
CONFIG = {
    "model": "models/gemini-2.5-flash",
    "temperature": 0.3,
    "max_tokens": 2048,
}
```

The module-level variable approach has one advantage for our use case: type
hints. `MODEL: str = "..."` clearly documents that `MODEL` is a string.
`CONFIG["model"]` requires reading the value to infer the type.

The dict approach has one advantage: you can pass `CONFIG` as a single argument
to functions that need all settings, rather than importing each variable separately.

Neither is universally better — the choice depends on how configuration is used.

---

## 14.5 **kwargs in Depth

We introduced `**kwargs` in Chapter 5. Here we examine it more completely.

**The single asterisk `*args`:**

`*args` collects positional arguments into a tuple:

```python
def add(*numbers):
    return sum(numbers)

add(1, 2, 3)      # numbers = (1, 2, 3) → returns 6
add(10, 20)       # numbers = (10, 20)  → returns 30
add()             # numbers = ()        → returns 0
```

**The double asterisk `**kwargs`:**

`**kwargs` collects keyword arguments into a dict:

```python
def show(**details):
    for key, value in details.items():
        print(f"{key}: {value}")

show(name="Nilton", role="Analyst")
# details = {"name": "Nilton", "role": "Analyst"}
# prints:
# name: Nilton
# role: Analyst
```

**Combining both:**

```python
def flexible(*args, **kwargs):
    print(f"positional: {args}")
    print(f"keyword:    {kwargs}")

flexible(1, 2, "hello", name="Nilton", debug=True)
# positional: (1, 2, 'hello')
# keyword:    {'name': 'Nilton', 'debug': True}
```

**Using `**` to unpack a dict into keyword arguments:**

The `**` operator also works in the other direction — unpacking a dict into
keyword arguments when calling a function:

```python
params = {"temperature": 0.9, "max_output_tokens": 512}

# These two calls are equivalent:
create_config(temperature=0.9, max_output_tokens=512)
create_config(**params)
```

This is useful when you have configuration in a dict and want to pass it to
a function that accepts keyword arguments.

**In `create_config()`:**

```python
def create_config(**overrides) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=overrides.get("temperature", TEMPERATURE),
        max_output_tokens=overrides.get("max_output_tokens", MAX_TOKENS),
    )
```

`overrides` is the dict of any keyword arguments passed. `.get(key, default)`
safely retrieves each value, falling back to the config.py default when not
provided. The result is a clean, extensible way to override defaults:

```python
# Use all defaults
create_config()

# Override one
create_config(temperature=1.2)

# Override multiple
create_config(temperature=0.0, max_output_tokens=128)
```

---

## 14.6 dict.get() vs dict[] — A Deeper Look

```python
d = {"name": "Nilton"}

d["name"]              # → "Nilton"
d["age"]               # → KeyError: 'age'

d.get("name")          # → "Nilton"
d.get("age")           # → None (no default provided)
d.get("age", 0)        # → 0 (explicit default)
```

**When to use `[]`:** When the key must exist and its absence is a bug.
The `KeyError` tells you immediately that something is wrong.

**When to use `.get()`:** When the key might legitimately be absent
and you have a sensible default. Configuration and option dictionaries
almost always use `.get()`.

In `create_config(**overrides)`, using `.get()` is correct because
`overrides` might be empty (no keyword arguments passed) — that is not
a bug, it just means "use all defaults."

---

# Chapter 15: Packages, __init__.py, and Relative Imports

## 15.1 The Python Import System

When you write `import something` or `from something import name`, Python
goes through a search process:

1. Check `sys.modules` (cache of already-imported modules) — if found, use it
2. Search `sys.path` — a list of directories where Python looks for modules
3. In each directory, look for `something.py` (a module) or `something/` with
   `__init__.py` (a package)
4. Execute the found file and cache the result in `sys.modules`

`sys.path` typically includes:
- The directory of the script being run
- Standard library directories
- Site-packages (where pip installs third-party packages)

This is why `from config import API_KEY` works when you run `python main.py`
from the project directory — `config.py` is in the same directory as `main.py`,
which is in `sys.path`.

---

## 15.2 What __init__.py Actually Does

When Python imports a package (a directory), it executes `__init__.py` first.
Whatever names are defined or imported in `__init__.py` become attributes of
the package.

**Scenario: no `__init__.py` re-exports**

```python
# gemini/__init__.py is empty

# In main.py:
from gemini import safe_chat   # ImportError: cannot import name 'safe_chat'
# safe_chat is in gemini/errors.py, not in gemini/__init__.py
```

**Scenario: `__init__.py` re-exports names**

```python
# gemini/__init__.py
from gemini.errors import safe_chat, safe_stream_chat, safe_multi_turn_chat

# In main.py:
from gemini import safe_chat   # Works! __init__.py brought it into the package namespace
```

The re-export in `__init__.py` is a design decision: the package presents a
clean public interface, and callers don't need to know which internal file
each function lives in.

---

## 15.3 __all__: Declaring the Public Interface

```python
# gemini/__init__.py
__all__ = [
    "safe_chat",
    "safe_stream_chat",
    "safe_multi_turn_chat",
    "simple_chat",
    "stream_chat",
    "multi_turn_chat",
    "create_client",
    "create_config",
]
```

**`__all__` controls `from package import *`:**

```python
from gemini import *
# Imports only names in __all__
# safe_chat, safe_stream_chat, etc. are now available
# Nothing else from the package is imported
```

Without `__all__`, `from gemini import *` would import everything that doesn't
start with an underscore — potentially hundreds of names from imported modules,
cluttering the namespace.

**`__all__` as documentation:**

Even if you never use `from gemini import *`, `__all__` serves as explicit
documentation of the intended public API. A developer reading `__init__.py`
immediately knows which functions are for external use.

**`__all__` does not prevent direct access:**

```python
# This still works even if '_handle_error' is not in __all__
from gemini.errors import _handle_error  # works, just unconventional
```

`__all__` is a communication tool, not a security mechanism.

---

## 15.4 Absolute vs. Relative Imports

**Absolute import** — specifies the full path from the project root:

```python
from gemini.errors import safe_chat        # full path
from config import API_KEY                  # from project root
```

**Relative import** — specifies the path relative to the current file's location,
using dots:

```python
# Inside gemini/errors.py:
from .operations import simple_chat         # same package (gemini/)
from .client import create_client           # same package (gemini/)

# . means "same package"
# .. means "parent package"
# ... means "grandparent package"
```

**Why use relative imports inside packages?**

1. **Independence from project name:** If you rename the project folder from
   `llm-api-client` to `gemini-client`, absolute imports like
   `from gemini.errors import ...` still work, but if the package itself were
   renamed, relative imports would still work while absolute ones might break.

2. **Clarity of intent:** `from .client import create_client` immediately
   communicates "this import is from within the same package."

3. **Refactoring safety:** If the package is moved, relative imports continue
   to work without modification.

**When NOT to use relative imports:**

At the top level (not inside a package), relative imports don't make sense.
`main.py` uses absolute imports:

```python
# main.py — correct
from gemini import safe_chat, safe_stream_chat, safe_multi_turn_chat
```

Not:

```python
# main.py — wrong (not inside a package)
from .gemini import safe_chat   # would fail
```

---

## 15.5 How the gemini/ Package Import Chain Works

When `main.py` runs `from gemini import safe_chat`, here is exactly what happens:

```
1. Python looks for 'gemini' in sys.modules — not found (first import)

2. Python searches sys.path for 'gemini'
   → finds gemini/ directory in the project root

3. Python checks for gemini/__init__.py
   → found — this is a package

4. Python executes gemini/__init__.py:

   Line: from gemini.errors import safe_chat, ...
   → Python needs to import gemini.errors
   → executes gemini/errors.py:

       Line: from .operations import simple_chat, ...
       → Python needs to import gemini.operations
       → executes gemini/operations.py:

           Line: from .client import create_client, create_config
           → Python needs to import gemini.client
           → executes gemini/client.py:

               Line: from config import API_KEY, ...
               → Python executes config.py:

                   Line: from my_api_keys import MY_GOOGLE_API_KEY
                   → Python executes my_api_keys.py
                   → MY_GOOGLE_API_KEY is now defined

               → config.py finishes — API_KEY, MODEL, etc. are defined

           → gemini/client.py finishes — create_client, create_config defined

       → gemini/operations.py finishes — simple_chat, stream_chat, multi_turn_chat defined

   → gemini/errors.py finishes — safe_chat, safe_stream_chat, safe_multi_turn_chat defined

   Line: from gemini.operations import simple_chat, ...
   → already in sys.modules cache — reused, not re-executed

   Line: from gemini.client import create_client, create_config
   → already in sys.modules cache — reused, not re-executed

5. gemini/__init__.py finishes
   → gemini package is now fully initialized
   → safe_chat is available as gemini.safe_chat

6. main.py: `safe_chat` is now bound in main.py's namespace
```

This cascade — each file triggering the imports of the files it depends on —
is how Python builds the complete dependency tree before running any application
code. The `sys.modules` cache ensures each file is executed only once,
no matter how many times it is imported.

---

## 15.6 The Package as an Abstraction Boundary

The `gemini/` package is an **abstraction boundary** — a wall between the
outside world (main.py) and the internal implementation (client.py, operations.py,
errors.py).

From `main.py`'s perspective:
- The `gemini` package has `safe_chat`, `safe_stream_chat`, `safe_multi_turn_chat`
- These functions accept strings and dicts and return dicts
- Nothing else needs to be known

This means you could completely rewrite the internals of `gemini/` — change the
SDK, restructure the files, rename internal functions — and `main.py` would not
need to change at all, as long as the three safe wrapper functions continue to
work the same way.

This property — the ability to change internals without affecting external callers —
is called **encapsulation** at the module level.

---

# Chapter 16: if __name__ == "__main__" and Entry Points

## 16.1 The __name__ Variable

Every Python module has a built-in variable called `__name__`. Its value depends
on how the module was loaded:

**When a file is run directly:**
```bash
python main.py
```
Python sets `__name__ = "__main__"` for that file.

**When a file is imported:**
```python
import main              # in some other file
from main import header  # or this
```
Python sets `__name__ = "main"` (the module name, without `.py`).

This distinction lets you write code that behaves differently depending on
whether it is the program's entry point or a module being used by something else.

---

## 16.2 The Pattern and Why It Exists

```python
# main.py

def demo_simple_chat() -> None:
    ...

def demo_streaming() -> None:
    ...

if __name__ == "__main__":
    # This block only runs when you execute: python main.py
    # It does NOT run when main.py is imported by another file
    demos = {"1": demo_simple_chat, "2": demo_streaming, "3": demo_multi_turn}
    choice = input("Select demo: ").strip()
    if choice in demos:
        demos[choice]()
```

**Without this pattern:**

```python
# main.py WITHOUT the guard

def demo_simple_chat() -> None:
    ...

# This runs unconditionally — even during import!
demos = {"1": demo_simple_chat, "2": demo_streaming, "3": demo_multi_turn}
choice = input("Select demo: ").strip()   # ← input() fires during import!
```

If another script imports `main.py` to reuse `demo_simple_chat`:

```python
# test_main.py
from main import demo_simple_chat   # ← triggers input() call — bad!
```

The `if __name__ == "__main__"` guard prevents the interactive menu from
running during import. The demo functions remain importable and reusable;
only the menu logic is restricted to direct execution.

---

## 16.3 Dunder Names: Python's Reserved Namespace

`__name__`, `__main__`, `__init__`, `__all__` all follow the same pattern:
double underscores on both sides. These are called **dunder** names
("dunder" = "double underscore").

Python uses dunder names for built-in attributes and special methods. You
have encountered several:

| Dunder name | Where | What it does |
|---|---|---|
| `__name__` | Every module | Contains the module's name, or `"__main__"` |
| `__init__.py` | Package directory | Marks directory as package; runs on import |
| `__all__` | Any module | Declares the public API for `import *` |
| `__init__` | Class method | Called when a new instance is created |
| `__str__` | Class method | Called by `str(obj)` and `print(obj)` |
| `__len__` | Class method | Called by `len(obj)` |
| `__name__` (on class) | Class attribute | The class's name as a string |

**The rule:** Never create your own names with double underscores on both sides.
That namespace belongs to Python. Use single leading underscores for private
names you define yourself: `_my_private_helper`.

---

## 16.4 Entry Points in Practice

An **entry point** is the file (and sometimes the function within it) that
starts program execution. In this project, `main.py` is the entry point:

```bash
python main.py
```

In larger Python projects, entry points are often declared explicitly in
`pyproject.toml` or `setup.py`, allowing them to be installed as command-line
tools:

```toml
# pyproject.toml (for a hypothetical packaged version)
[project.scripts]
llm-chat = "main:run"   # installs a 'llm-chat' command that calls main.run()
```

For a local project run with `python main.py`, this is unnecessary. But
understanding that entry points are a concept — not just a convention — helps
when you encounter packages that install command-line tools.

---

## 16.5 Module-Level Code and Import Side Effects

Everything outside a function or class in a Python file is **module-level code**.
It runs when the module is imported, regardless of the `if __name__` guard.

In `config.py`:

```python
from my_api_keys import MY_GOOGLE_API_KEY   # ← runs on import

API_KEY: str = MY_GOOGLE_API_KEY            # ← runs on import
MODEL: str = "models/gemini-2.5-flash"     # ← runs on import
```

These execute when `config.py` is first imported. This is intentional — the
constants need to be defined immediately so any module that imports them finds
them ready.

**Side effects to avoid at module level:**

Module-level code that has side effects — making network requests, opening files,
prompting for input, modifying global state — is generally considered bad practice
because it runs unconditionally during import, even in contexts where you
don't want it to:

```python
# Bad — side effect at module level
import requests
data = requests.get("https://api.example.com/config").json()  # fires on import!

# Good — side effect inside a function, called only when needed
def load_config():
    return requests.get("https://api.example.com/config").json()
```

In `list_models.py`, we intentionally put the API call at the module level
because that file is always run directly, never imported:

```python
# list_models.py
client = genai.Client(api_key=API_KEY)
for model in client.models.list():
    print(f"  {model.name}")
```

This is acceptable for a utility script. For any module that might be imported,
wrap side-effecting code in functions and call them explicitly.

---

## 16.6 Reviewing main.py Through the Lens of This Chapter

```python
# main.py

# ── Module-level imports ──────────────────────────────────────────────────────
# These run immediately when main.py is imported or executed directly.
# They have no side effects — just loading names into the namespace.
from gemini import safe_chat, safe_stream_chat, safe_multi_turn_chat


# ── Function definitions ──────────────────────────────────────────────────────
# These are defined at module level but do NOT run yet.
# Functions are objects — defining them just creates the object.
def header(title: str) -> None:
    print(f"\n{'=' * 60}\n  {title}\n{'=' * 60}")

def footer(info: str = "") -> None:
    if info:
        print(f"\n  ℹ {info}")
    print("─" * 60)

def demo_simple_chat() -> None:
    ...   # defined but not called

def demo_streaming() -> None:
    ...   # defined but not called

def demo_multi_turn() -> None:
    ...   # defined but not called


# ── Entry point guard ────────────────────────────────────────────────────────
# Only executes when python main.py is run directly.
if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("  GEMINI API CLIENT — MODULAR DEMO")
    print("=" * 60)

    print("\nSelect a demo:")
    print("  1. Simple Chat     — single question, full response")
    print("  2. Streaming       — single question, token-by-token output")
    print("  3. Multi-turn Chat — conversation with accumulated context")

    choice = input("\nEnter the demo number: ").strip()

    demos = {              # dispatch table
        "1": demo_simple_chat,
        "2": demo_streaming,
        "3": demo_multi_turn,
    }

    if choice in demos:
        demos[choice]()   # look up and call
    else:
        print(f"Invalid choice: '{choice}'. Please enter 1, 2, or 3.")

    print("\nDone.\n")
```

All the concepts from this Part appear here:
- Type annotations on every function
- Dicts for the dispatch table
- Functions as first-class values (`demo_simple_chat` stored in dict)
- `__name__ == "__main__"` guarding the entry point
- Module-level imports with no side effects
- Function definitions that don't execute until called

---

## Part 5 Summary

| Concept | One-line summary |
|---|---|
| Type hints | Annotations documenting expected types — not enforced at runtime |
| `str`, `int`, `float`, `bool` | The four basic built-in types |
| `-> None` | Return annotation for functions that produce side effects only |
| Union type (`str \| None`) | A value that can be one of several types |
| `Callable[[str], None]` | Type hint for a function accepting str and returning None |
| Dict | Key-value collection; keys are unique and hashable |
| `dict.get(key, default)` | Safe lookup — returns default if key is missing |
| Dispatch table | Dict mapping keys to function objects for clean branching |
| First-class functions | Functions can be stored in variables, dicts, passed as args |
| `fn` vs `fn()` | Function object vs. function call |
| `*args` | Collects positional arguments into a tuple |
| `**kwargs` | Collects keyword arguments into a dict |
| `**dict` unpacking | Expands a dict into keyword arguments in a function call |
| `__init__.py` | Marks directory as package; runs on import; re-exports public names |
| `__all__` | Declares the public API; controls `from package import *` |
| Absolute import | Full path from project root: `from gemini.errors import ...` |
| Relative import | Path relative to current package: `from .client import ...` |
| `sys.modules` | Cache of imported modules — each file executes only once |
| Abstraction boundary | Package hides its internals; callers depend on interface only |
| `__name__` | Module attribute: `"__main__"` when run directly, module name when imported |
| `if __name__ == "__main__"` | Runs only when file is executed directly, not imported |
| Dunder names | `__x__` names reserved for Python's built-in system |
| Module-level code | Executes on import — keep it side-effect free in importable modules |
| Entry point | The file (and function) where program execution begins |

---

*Next: Part 6 — Putting It All Together (Chapters 17, 18, and 19)*
*Reading the full project, how to extend it, and what to study next.*

