"""
Gauntlet task definitions for Cognitive Core Gen-2.

Each task is a dict with:
  - id: unique task ID (e.g. "M01-001")
  - gauntlet: gauntlet family (e.g. "M01", "LCTX01")
  - prompt: the prompt to send to the model
  - chat_template: "minicpm" or "qwen" — which chat format to use
  - evaluator: name of the evaluation function to apply
  - expected: expected answer/data for the evaluator
  - max_tokens: max generation tokens
  - difficulty: "basic" | "intermediate" | "advanced"
  - tags: list of capability tags

Evaluator functions are defined in gauntlet_evaluators.py.
"""

# M01 — Structural Identity tasks
# Tests whether the model can recognise structurally identical procedures
# despite cosmetic differences (renaming, reformatting).

M01_TASKS = [
    {
        "id": "M01-001",
        "gauntlet": "M01",
        "prompt": "Procedure A:\n1. Read input file\n2. Validate format\n3. Transform data\n4. Write output\n\nProcedure B:\n1. Read input file\n2. Validate format\n3. Transform data\n4. Write output\n\nAre procedures A and B structurally equivalent? Answer with exactly one word: yes or no.",
        "chat_template": "minicpm",
        "evaluator": "exact_match",
        "expected": "yes",
        "max_tokens": 5,
        "difficulty": "basic",
        "tags": ["structural_identity", "equivalence"]
    },
    {
        "id": "M01-002",
        "gauntlet": "M01",
        "prompt": "Procedure A:\n1. Read input file\n2. Validate format\n3. Transform data\n4. Write output\n\nProcedure B:\n1. Read input file\n2. Validate format\n3. Log results\n4. Write output\n\nAre procedures A and B structurally equivalent? Answer with exactly one word: yes or no.",
        "chat_template": "minicpm",
        "evaluator": "exact_match",
        "expected": "no",
        "max_tokens": 5,
        "difficulty": "basic",
        "tags": ["structural_identity", "difference_detection"]
    },
    {
        "id": "M01-003",
        "gauntlet": "M01",
        "prompt": "Snippet A:\ndef process(data):\n    cleaned = data.strip().lower()\n    result = cleaned.split(',')\n    return [x for x in result if x]\n\nSnippet B:\ndef process(d):\n    c = d.strip().lower()\n    r = c.split(',')\n    return [x for x in r if x]\n\nDo these two snippets do the same thing? Answer with exactly one word: yes or no.",
        "chat_template": "minicpm",
        "evaluator": "exact_match",
        "expected": "yes",
        "max_tokens": 5,
        "difficulty": "intermediate",
        "tags": ["structural_identity", "renaming"]
    },
    {
        "id": "M01-004",
        "gauntlet": "M01",
        "prompt": "Snippet A:\ndef process(data):\n    cleaned = data.strip().lower()\n    result = cleaned.split(',')\n    return [x for x in result if x]\n\nSnippet B:\ndef process(data):\n    cleaned = data.strip().upper()\n    result = cleaned.split(',')\n    return [x for x in result if x]\n\nDo these two snippets do the same thing? Answer with exactly one word: yes or no.",
        "chat_template": "minicpm",
        "evaluator": "exact_match",
        "expected": "no",
        "max_tokens": 5,
        "difficulty": "intermediate",
        "tags": ["structural_identity", "semantic_difference"]
    },
]

# LCTX01 — One Needle tasks
# Tests whether the model can recall a single fact from context.

LCTX01_TASKS = [
    {
        "id": "LCTX01-001",
        "gauntlet": "LCTX01",
        "prompt": "Here is some text:\n\nThe quick brown fox jumps over the lazy dog. The capital of France is Paris. The speed of light is approximately 299,792,458 metres per second. Water freezes at 0 degrees Celsius.\n\nQuestion: What is the capital of France?",
        "chat_template": "minicpm",
        "evaluator": "contains",
        "expected": "Paris",
        "max_tokens": 20,
        "difficulty": "basic",
        "tags": ["retrieval", "fact_recall"]
    },
    {
        "id": "LCTX01-002",
        "gauntlet": "LCTX01",
        "prompt": "Here is some data:\n\nUser ID: 8472\nUsername: jake_cognitive\nRole: researcher\nLast login: 2026-08-17\nProject: Cognitive Core Gen-2\nAccess level: admin\n\nQuestion: What is the access level of user jake_cognitive?",
        "chat_template": "minicpm",
        "evaluator": "contains",
        "expected": "admin",
        "max_tokens": 20,
        "difficulty": "basic",
        "tags": ["retrieval", "structured_data"]
    },
    {
        "id": "LCTX01-003",
        "gauntlet": "LCTX01",
        "prompt": "Below is a conversation history. Read it carefully.\n\nUser: Can you help me set up my development environment?\nAssistant: Sure! What tools do you need?\nUser: I need Python 3.11, Docker, and VS Code.\nAssistant: Great. Python 3.11 is available via pyenv. Docker Desktop is also available. VS Code can be installed via brew.\nUser: What's the command for VS Code?\nAssistant: The command is: brew install --cask visual-studio-code\n\nQuestion: What command did the assistant give for installing VS Code?",
        "chat_template": "minicpm",
        "evaluator": "contains",
        "expected": "brew install --cask visual-studio-code",
        "max_tokens": 30,
        "difficulty": "basic",
        "tags": ["retrieval", "conversation"]
    },
]

# LCTX02 — Many Needles tasks
# Tests retrieval of multiple items from context.

LCTX02_TASKS = [
    {
        "id": "LCTX02-001",
        "gauntlet": "LCTX02",
        "prompt": "Here are several facts:\n\n1. Mercury is the smallest planet.\n2. Venus is the hottest planet.\n3. Earth is the third planet from the Sun.\n4. Mars is known as the Red Planet.\n5. Jupiter is the largest planet.\n\nQuestion: Name the largest planet and the hottest planet.",
        "chat_template": "minicpm",
        "evaluator": "contains_all",
        "expected": ["Jupiter", "Venus"],
        "max_tokens": 30,
        "difficulty": "basic",
        "tags": ["retrieval", "multi_fact"]
    },
    {
        "id": "LCTX02-002",
        "gauntlet": "LCTX02",
        "prompt": "Project TODO list:\n- [ ] Implement user authentication (assigned to: Alice)\n- [ ] Write API documentation (assigned to: Bob)\n- [ ] Set up CI/CD pipeline (assigned to: Charlie)\n- [x] Database schema design (completed by: Alice)\n- [x] Initial project setup (completed by: Jake)\n\nQuestion: Who is assigned to implement user authentication, and who is assigned to set up CI/CD?",
        "chat_template": "minicpm",
        "evaluator": "contains_all",
        "expected": ["Alice", "Charlie"],
        "max_tokens": 30,
        "difficulty": "basic",
        "tags": ["retrieval", "multi_fact", "structured"]
    },
]

# LCTX03 — Multi-Hop tasks
# Tests chaining facts together across context.

LCTX03_TASKS = [
    {
        "id": "LCTX03-001",
        "gauntlet": "LCTX03",
        "prompt": "Facts:\n- Alice manages the Engineering team.\n- Bob reports to Alice.\n- Charlie reports to Bob.\n- Diana reports to Charlie.\n\nQuestion: Who is two levels of management above Diana? Let's trace it: Diana reports to Charlie. Charlie reports to Bob. So Bob is one level above, and who reports to Bob? That person is two levels above Diana. Answer with just the name.",
        "chat_template": "minicpm",
        "evaluator": "contains",
        "expected": "Bob",
        "max_tokens": 30,
        "difficulty": "intermediate",
        "tags": ["multi_hop", "reasoning"]
    },
    {
        "id": "LCTX03-002",
        "gauntlet": "LCTX03",
        "prompt": "Warehouse A:\n- 10 boxes of screws, each weighs 2 kg\n- 8 boxes of nails, each weighs 1.5 kg\n- 5 boxes of bolts, each weighs 3 kg\n\nQuestion: What is the total weight of all boxes in Warehouse A?\nCalculation: (10 x 2) + (8 x 1.5) + (5 x 3) = ?",
        "chat_template": "minicpm",
        "evaluator": "contains",
        "expected": "47",
        "max_tokens": 50,
        "difficulty": "intermediate",
        "tags": ["multi_hop", "computation"]
    },
]

# SA01 — Multi-Session State Continuity tasks
# Tests state tracking across context boundaries.

SA01_TASKS = [
    {
        "id": "SA01-001",
        "gauntlet": "SA01",
        "prompt": "Session 1:\nUser: Start a new project called 'Project Phoenix'.\nAssistant: Project Phoenix created. Current directory: /projects/phoenix\nUser: Set the language to Python.\nAssistant: Language set to Python.\nUser: Add a task: 'Design database schema'.\nAssistant: Task added.\n\nSession 2:\nThe same user returns later. User: What is my current project called, and what language is it using?",
        "chat_template": "minicpm",
        "evaluator": "contains_all",
        "expected": ["Phoenix", "Python"],
        "max_tokens": 50,
        "difficulty": "basic",
        "tags": ["state", "continuity"]
    },
    {
        "id": "SA01-002",
        "gauntlet": "SA01",
        "prompt": "Configuration changes over time:\n\nDay 1: Theme=dark, FontSize=14, Notifications=enabled\nDay 2: FontSize changed to 16, Language set to English\nDay 3: Notifications set to disabled, AutoSave enabled\n\nQuestion: What are the final values for Theme, FontSize, Notifications, and Language?",
        "chat_template": "minicpm",
        "evaluator": "contains_all",
        "expected": ["dark", "16", "disabled", "English"],
        "max_tokens": 50,
        "difficulty": "intermediate",
        "tags": ["state", "latest_value"]
    },
]


def get_gauntlet_id(task: dict) -> str:
    """Extract the gauntlet ID (e.g. 'M01') from a task."""
    return task["gauntlet"]


def all_tasks() -> list:
    """Return all available tasks."""
    return M01_TASKS + LCTX01_TASKS + LCTX02_TASKS + LCTX03_TASKS + SA01_TASKS


def tasks_by_gauntlet(gauntlet_id: str) -> list:
    """Return tasks for a specific gauntlet."""
    return [t for t in all_tasks() if t["gauntlet"] == gauntlet_id]


def tasks_by_difficulty(difficulty: str) -> list:
    """Return tasks at a specific difficulty level."""
    return [t for t in all_tasks() if t["difficulty"] == difficulty]


def tasks_by_tag(tag: str) -> list:
    """Return tasks with a specific tag."""
    return [t for t in all_tasks() if tag in t["tags"]]


def export_jsonl(path: str, task_list: list = None):
    """Export tasks to a JSONL file."""
    import json
    tasks = task_list or all_tasks()
    with open(path, "w") as f:
        for t in tasks:
            f.write(json.dumps(t) + "\n")
    print(f"Exported {len(tasks)} tasks to {path}")


if __name__ == "__main__":
    base = "/Users/jake/Projects/cognitive core"
    # Export all tasks to JSONL
    export_jsonl(f"{base}/gauntlets/tasks.jsonl")
    # Also export per-gauntlet
    for gid in ["M01", "LCTX01", "LCTX02", "LCTX03", "SA01"]:
        export_jsonl(f"{base}/gauntlets/{gid.lower()}-tasks.jsonl", tasks_by_gauntlet(gid))
    print(f"\nTotal tasks: {len(all_tasks())}")
    print(f"By gauntlet:")
    for gid in ["M01", "LCTX01", "LCTX02", "LCTX03", "SA01"]:
        print(f"  {gid}: {len(tasks_by_gauntlet(gid))} tasks")
    print(f"By difficulty:")
    for d in ["basic", "intermediate", "advanced"]:
        count = len(tasks_by_difficulty(d))
        if count:
            print(f"  {d}: {count} tasks")