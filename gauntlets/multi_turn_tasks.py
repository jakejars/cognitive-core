"""
Multi-Turn Gauntlet Tasks — Cognitive Core Gen-2

These tasks span multiple conversation turns and test the system's
ability to maintain state, track updates, and use external memory.

Key gauntlets:
  MT01 — Fact retention across turns
  MT02 — State updates and latest-value tracking
  MT03 — Supersession / contradiction resolution
  MT04 — Accumulated context (growing history)
  MT05 — Distractor resistance across turns

Each task is a list of turns. The first turn(s) provide context,
the final turn asks a question that depends on prior turns.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Turn:
    """A single turn in a multi-turn conversation."""
    role: str  # "user" or "assistant"
    content: str
    is_question: bool = False  # Is this the final eval turn?
    expected_answer: str = ""
    evaluator: str = "contains"


@dataclass
class MultiTurnTask:
    """A multi-turn task with conversation history and final evaluation."""
    id: str
    gauntlet: str
    turns: List[Turn]
    difficulty: str = "basic"
    tags: List[str] = field(default_factory=list)
    max_tokens: int = 100


# MT01 — Fact retention across turns
# Tests whether the model remembers facts stated in earlier turns.

MT01_TASKS = [
    MultiTurnTask(
        id="MT01-001",
        gauntlet="MT01",
        difficulty="basic",
        tags=["memory", "retention", "cross_turn"],
        max_tokens=30,
        turns=[
            Turn("user", "My name is Alex and I work as a data scientist."),
            Turn("assistant", "Nice to meet you, Alex! Data science is fascinating."),
            Turn("user", "I also have a pet cat named Whiskers."),
            Turn("assistant", "That's great! Cats make wonderful companions."),
            Turn("user", "What is my name and what is my pet's name?",
                 is_question=True, expected_answer="Alex", evaluator="contains_all"),
        ],
    ),
    MultiTurnTask(
        id="MT01-002",
        gauntlet="MT01",
        difficulty="basic",
        tags=["memory", "retention", "cross_turn"],
        max_tokens=30,
        turns=[
            Turn("user", "Set my theme to dark mode."),
            Turn("assistant", "Theme set to dark mode."),
            Turn("user", "Set font size to 14."),
            Turn("assistant", "Font size set to 14."),
            Turn("user", "What are my current settings?",
                 is_question=True, expected_answer="dark, 14, dark mode",
                 evaluator="contains"),
        ],
    ),
    MultiTurnTask(
        id="MT01-003",
        gauntlet="MT01",
        difficulty="intermediate",
        tags=["memory", "retention", "cross_turn"],
        max_tokens=50,
        turns=[
            Turn("user", "My project is called 'Nebula' and it's about image recognition."),
            Turn("assistant", "Nebula sounds interesting! Image recognition has many applications."),
            Turn("user", "The tech stack is Python with PyTorch."),
            Turn("assistant", "Good choices."),
            Turn("user", "I'm using a ResNet-50 architecture."),
            Turn("assistant", "ResNet-50 is a solid choice for image recognition."),
            Turn("user", "Tell me about my project. What is it called, what tech stack, and what architecture?",
                 is_question=True, expected_answer=["Nebula", "Python", "PyTorch", "ResNet"],
                 evaluator="contains_all"),
        ],
    ),
]

# MT02 — State updates and latest-value tracking
# Tests whether the model correctly tracks the LATEST value after updates.

MT02_TASKS = [
    MultiTurnTask(
        id="MT02-001",
        gauntlet="MT02",
        difficulty="basic",
        tags=["state", "updates", "latest_value"],
        max_tokens=30,
        turns=[
            Turn("user", "Set my email to old_email@example.com."),
            Turn("assistant", "Email set."),
            Turn("user", "Set my email to new_email@example.com."),
            Turn("assistant", "Email updated."),
            Turn("user", "What is my current email?",
                 is_question=True, expected_answer="new_email@example.com",
                 evaluator="contains"),
        ],
    ),
    MultiTurnTask(
        id="MT02-002",
        gauntlet="MT02",
        difficulty="intermediate",
        tags=["state", "updates", "latest_value", "multiple_fields"],
        max_tokens=50,
        turns=[
            Turn("user", "My name is Sam, language is English, topic is science."),
            Turn("assistant", "Profile created."),
            Turn("user", "Change language to French."),
            Turn("assistant", "Language updated to French."),
            Turn("user", "Change name to Samantha."),
            Turn("assistant", "Name updated to Samantha."),
            Turn("user", "What are my current name and language settings?",
                 is_question=True, expected_answer=["Samantha", "French"],
                 evaluator="contains_all"),
        ],
    ),
    MultiTurnTask(
        id="MT02-003",
        gauntlet="MT02",
        difficulty="intermediate",
        tags=["state", "updates", "counter"],
        max_tokens=30,
        turns=[
            Turn("user", "Count starts at 0. Add 5."),
            Turn("assistant", "Count is now 5."),
            Turn("user", "Add 3."),
            Turn("assistant", "Count is now 8."),
            Turn("user", "Subtract 2."),
            Turn("assistant", "Count is now 6."),
            Turn("user", "What is the current count?",
                 is_question=True, expected_answer="6", evaluator="contains"),
        ],
    ),
]

# MT03 — Supersession / contradiction resolution
# Tests whether the model recognizes when new info supersedes old.

MT03_TASKS = [
    MultiTurnTask(
        id="MT03-001",
        gauntlet="MT03",
        difficulty="intermediate",
        tags=["supersession", "contradiction"],
        max_tokens=30,
        turns=[
            Turn("user", "The meeting is on Tuesday at 2pm."),
            Turn("assistant", "Meeting scheduled for Tuesday 2pm."),
            Turn("user", "Actually, move the meeting to Wednesday at 3pm."),
            Turn("assistant", "Meeting rescheduled to Wednesday 3pm."),
            Turn("user", "What day and time is the meeting now?",
                 is_question=True, expected_answer=["Wednesday", "3pm"],
                 evaluator="contains_all"),
        ],
    ),
    MultiTurnTask(
        id="MT03-002",
        gauntlet="MT03",
        difficulty="advanced",
        tags=["supersession", "contradiction", "partial_update"],
        max_tokens=50,
        turns=[
            Turn("user", "The file is in /home/user/documents/report.pdf"),
            Turn("assistant", "File location noted."),
            Turn("user", "Actually, I moved it to /home/user/archive/report.pdf"),
            Turn("assistant", "Location updated."),
            Turn("user", "Also renamed it to final_report.pdf"),
            Turn("assistant", "Name updated."),
            Turn("user", "What is the current full path of the file?",
                 is_question=True, expected_answer="/home/user/archive/final_report.pdf",
                 evaluator="contains"),
        ],
    ),
]

# MT04 — Accumulated context
# Tests the ability to answer questions from growing context.

MT04_TASKS = [
    MultiTurnTask(
        id="MT04-001",
        gauntlet="MT04",
        difficulty="basic",
        tags=["accumulation", "growing_context"],
        max_tokens=30,
        turns=[
            Turn("user", "Task 1: Buy groceries."),
            Turn("assistant", "Task 1 added: Buy groceries."),
            Turn("user", "Task 2: Finish report."),
            Turn("assistant", "Task 2 added: Finish report."),
            Turn("user", "Task 3: Call dentist."),
            Turn("assistant", "Task 3 added: Call dentist."),
            Turn("user", "List all my tasks.",
                 is_question=True, expected_answer=["groceries", "report", "dentist"],
                 evaluator="contains_all"),
        ],
    ),
    MultiTurnTask(
        id="MT04-002",
        gauntlet="MT04",
        difficulty="intermediate",
        tags=["accumulation", "ordered_list"],
        max_tokens=50,
        turns=[
            Turn("user", "Add item: Apples"),
            Turn("assistant", "Added: Apples"),
            Turn("user", "Add item: Bananas"),
            Turn("assistant", "Added: Bananas"),
            Turn("user", "Add item: Cherries at position 1"),
            Turn("assistant", "Added: Cherries at position 1"),
            Turn("user", "Add item: Dates"),
            Turn("assistant", "Added: Dates"),
            Turn("user", "What is the second item in my list?",
                 is_question=True, expected_answer="Bananas", evaluator="contains"),
        ],
    ),
]

# MT05 — Distractor resistance
# Tests focus amidst many turns of irrelevant chat.

MT05_TASKS = [
    MultiTurnTask(
        id="MT05-001",
        gauntlet="MT05",
        difficulty="advanced",
        tags=["distractor", "focus"],
        max_tokens=30,
        turns=[
            Turn("user", "I like hiking and climbing mountains."),
            Turn("assistant", "Great hobbies!"),
            Turn("user", "My favourite book is 'The Hobbit'."),
            Turn("assistant", "A classic!"),
            Turn("user", "I also enjoy cooking Italian food."),
            Turn("assistant", "Delicious!"),
            Turn("user", "The code for the safe is 3847."),
            Turn("assistant", "Safe code noted."),
            Turn("user", "I recently went to Japan on vacation."),
            Turn("assistant", "How wonderful!"),
            Turn("user", "What is the safe code?",
                 is_question=True, expected_answer="3847", evaluator="contains"),
        ],
    ),
]


def all_mt_tasks() -> List[MultiTurnTask]:
    return MT01_TASKS + MT02_TASKS + MT03_TASKS + MT04_TASKS + MT05_TASKS


def tasks_by_gauntlet(gid: str) -> List[MultiTurnTask]:
    return [t for t in all_mt_tasks() if t.gauntlet == gid]


def format_mt_prompt(turns: List[Turn], include_substrate_context: bool = False,
                     substrate_context: str = "") -> str:
    """
    Format multi-turn conversation into a single prompt.
    For evaluation, we feed all turns as context then ask the final question.
    """
    parts = []
    for i, turn in enumerate(turns):
        if turn.is_question:
            # This is the final evaluation question
            if include_substrate_context and substrate_context:
                parts.append(f"Remembered information from previous turns:\n{substrate_context}")
            parts.append(f"Question: {turn.content}")
        else:
            parts.append(f"{turn.role.capitalize()}: {turn.content}")
    
    return "\n\n".join(parts) if not any(t.is_question for t in turns) else "\n\n".join(parts)


def export_tasks():
    """Export multi-turn tasks to a readable format."""
    total = len(all_mt_tasks())
    print(f"Multi-turn tasks: {total}")
    by_g = {}
    for t in all_mt_tasks():
        by_g[t.gauntlet] = by_g.get(t.gauntlet, 0) + 1
    for g, c in sorted(by_g.items()):
        print(f"  {g}: {c} tasks ({sum(1 for t in all_mt_tasks() if t.gauntlet == g and t.difficulty == 'basic')} basic, {sum(1 for t in all_mt_tasks() if t.gauntlet == g and t.difficulty == 'intermediate')} intermediate, {sum(1 for t in all_mt_tasks() if t.gauntlet == g and t.difficulty == 'advanced')} advanced)")
    print(f"\nTotal turns across all tasks: {sum(len(t.turns) for t in all_mt_tasks())}")
    return total


if __name__ == "__main__":
    export_tasks()