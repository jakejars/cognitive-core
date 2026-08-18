"""
Long-Context Synthetic Data Generator

Generates long synthetic texts with planted facts ("needles") at specific
depth positions for evaluating memory retrieval.

From Memory Spec §17 (RULER-style), §22 (LCTX gauntlets):
  - Needles are planted at configurable depth positions
  - Filler text provides semantic distractor content
  - Supports contexts from 1K to 1M+ tokens
"""

import random
import hashlib
from typing import List, Dict, Tuple, Optional


# ── Filler text templates ──────────────────────────────────────────

FILLER_TOPICS = [
    "The history of maritime navigation in the Mediterranean",
    "Advances in quantum computing architectures",
    "The migration patterns of monarch butterflies",
    "Traditional fermentation techniques in East Asian cuisine",
    "The geology of volcanic island formation",
    "Renaissance art techniques in fresco painting",
    "The development of early programming languages",
    "Ecological restoration of coral reef systems",
    "The physics of supercooled liquids",
    "Mathematical foundations of cryptography",
]

FILLER_SENTENCES = [
    "Researchers have long studied the underlying principles governing {topic}, leading to significant advances in our understanding.",
    "A recent comprehensive survey examined over 200 case studies related to {topic}, revealing unexpected patterns.",
    "The practical applications of {topic} extend far beyond what early pioneers imagined possible.",
    "Historical records indicate that interest in {topic} dates back several centuries.",
    "Several competing theoretical frameworks exist to explain observations in {topic}.",
    "The economic impact of advances in {topic} has been estimated at billions of dollars annually.",
    "Educational programs focusing on {topic} have shown promising results in student engagement.",
    "Cross-disciplinary approaches combining {topic} with computer science have opened new research directions.",
    "The ethical implications of {topic} continue to be debated among experts in the field.",
    "Field studies conducted across multiple continents have validated key predictions about {topic}.",
    "Technological innovations have dramatically accelerated research into {topic} over the past decade.",
    "The relationship between {topic} and climate change is an area of active investigation.",
    "Several major universities have established dedicated research centres for {topic}.",
    "International collaboration has been essential to progress in understanding {topic}.",
    "The future of {topic} depends on training the next generation of skilled researchers.",
]

# ── Needle templates ──────────────────────────────────────────────

NEEDLE_TEMPLATES: Dict[str, List[str]] = {
    "fact": [
        "The {attribute} of the {entity} is {value}.",
        "According to records, {entity} has a {attribute} of {value}.",
        "It is well documented that {entity} possesses a {attribute} of {value}.",
        "The {entity} is known to have a {attribute} equal to {value}.",
    ],
    "code": [
        "The function {name} returns {value} when called with input {input_val}.",
        "In the codebase, {name}({input_val}) evaluates to {value}.",
        "The variable {name} is set to {value} in the configuration.",
    ],
    "event": [
        "On {date}, the {subject} {action} at {location}.",
        "The historical record shows that the {subject} {action} on {date}.",
        "Witnesses reported that the {subject} {action} at approximately {time}.",
    ],
}

FILLER_ENTITIES = [
    "Alpha-7 processor", "Zeta protocol", "Nexus database", "Quantum core",
    "Phoenix Framework", "Helix compiler", "Vertex API", "Cascade system",
    "Aurora platform", "Dynamo engine", "Fusion middleware", "Pulse network",
    "Titan repository", "Orbit scheduler", "Prism validator", "Vortex driver",
]

FILLER_ATTRIBUTES = [
    "maximum throughput", "latency threshold", "memory capacity", "core temperature",
    "processing speed", "bandwidth limit", "cache size", "power consumption",
    "error rate", "uptime percentage", "response time", "concurrent users",
    "data transfer rate", "compression ratio", "encryption strength", "batch size",
]


class LongContextGenerator:
    """
    Generates long synthetic texts with planted facts.

    Usage:
        gen = LongContextGenerator()
        context, needles = gen.generate(target_tokens=10000, num_needles=3)
    """

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def _fill_sentence(self) -> str:
        topic = self.rng.choice(FILLER_TOPICS)
        template = self.rng.choice(FILLER_SENTENCES)
        return template.format(topic=topic)

    def _fill_paragraph(self, target_words: int = 80) -> str:
        """Generate filler text of approximately target_words length."""
        words = 0
        sentences = []
        while words < target_words:
            sentence = self._fill_sentence()
            sentences.append(sentence)
            words += len(sentence.split())
        return " ".join(sentences)

    def _create_needle_fact(self, needle_id: str) -> str:
        """Create a unique fact needle."""
        entity = self.rng.choice(FILLER_ENTITIES)
        attribute = self.rng.choice(FILLER_ATTRIBUTES)
        value = f"{self.rng.randint(100, 9999)} {self.rng.choice(['units', 'ms', 'MB', 'GHz', 'W', '%', 'req/s'])}"

        template = self.rng.choice(NEEDLE_TEMPLATES["fact"])
        fact = template.format(entity=entity, attribute=attribute, value=value)

        return fact

    def _create_needle_code(self, needle_id: str) -> str:
        """Create a code-related needle."""
        name = f"compute_{needle_id}"
        input_val = self.rng.randint(0, 100)
        value = self.rng.randint(100, 99999)
        template = self.rng.choice(NEEDLE_TEMPLATES["code"])
        return template.format(name=name, input_val=input_val, value=value)

    def _create_needle_event(self, needle_id: str) -> str:
        """Create an event needle."""
        subject = f"{needle_id}-mission"
        action = self.rng.choice(["launched", "landed", "discovered", "established", "completed"])
        location = f"Site-{self.rng.randint(100, 999)}"
        date = f"2024-{self.rng.randint(1, 12):02d}-{self.rng.randint(1, 28):02d}"
        template = self.rng.choice(NEEDLE_TEMPLATES["event"])
        return template.format(date=date, subject=subject, action=action, location=location, time=date)

    def _count_tokens(self, text: str) -> int:
        """Approximate token count (whitespace split)."""
        return len(text.split())

    def generate(self, target_tokens: int, num_needles: int = 5,
                 needle_type: str = "fact",
                 depth_positions: Optional[List[float]] = None) -> Tuple[str, List[Dict]]:
        """
        Generate a long context with planted needles.

        Args:
            target_tokens: Approximate total token count
            num_needles: Number of facts to plant
            needle_type: 'fact', 'code', or 'event'
            depth_positions: List of floats 0.0-1.0 for needle positions.
                             Defaults to evenly distributed positions.

        Returns:
            (full_text, needle_info_list)
        """
        if depth_positions is None:
            # Distribute needles evenly through the text
            depth_positions = [(i + 1) / (num_needles + 1) for i in range(num_needles)]

        assert len(depth_positions) == num_needles, \
            f"Expected {num_needles} depths, got {len(depth_positions)}"

        # Create needles
        needles = []
        for i in range(num_needles):
            nid = f"NDL-{i+1:03d}"
            if needle_type == "code":
                text = self._create_needle_code(nid)
            elif needle_type == "event":
                text = self._create_needle_event(nid)
            else:
                text = self._create_needle_fact(nid)

            needles.append({
                "id": nid,
                "text": text,
                "depth": depth_positions[i],
                "query": self._needle_to_query(text),
            })

        # Sort needles by depth position
        needles.sort(key=lambda n: n["depth"])

        # Build the full context
        sections = []
        current_pos = 0.0
        total_filler_tokens = target_tokens - sum(self._count_tokens(n["text"]) for n in needles)
        filler_per_section = total_filler_tokens // (num_needles + 1)

        for needle in needles:
            # Add filler before this needle
            if filler_per_section > 0:
                sections.append(self._fill_paragraph(target_words=filler_per_section))
            # Add the needle
            sections.append(f"\n[NEEDLE {needle['id']}]\n{needle['text']}\n")

        # Add final filler
        if filler_per_section > 0:
            sections.append(self._fill_paragraph(target_words=filler_per_section))

        full_text = "\n\n".join(sections)

        # Update actual token counts
        for needle in needles:
            needle["position_tokens"] = self._find_needle_position(full_text, needle["text"])

        return full_text, needles

    def _needle_to_query(self, needle_text: str) -> str:
        """Generate a natural language query that the needle answers."""
        # Extract key entities
        for entity in FILLER_ENTITIES:
            if entity.lower() in needle_text.lower():
                # Find the attribute
                for attr in FILLER_ATTRIBUTES:
                    if attr in needle_text:
                        # Check for value pattern
                        import re
                        values = re.findall(r'(\d+)\s*(units|ms|MB|GHz|W|%|req/s)', needle_text)
                        if values:
                            return f"What is the {attr} of the {entity}?"
                        # Code value
                        values = re.findall(r'evaluates to (\d+)', needle_text)
                        if values:
                            return f"What does {entity} evaluate to?"
                return f"What is the value associated with {entity}?"
        return f"What information is stored about the entity in this text?"

    def _find_needle_position(self, full_text: str, needle_text: str) -> int:
        """Find approximate token position of a needle in the full text."""
        pos = full_text.find(needle_text)
        if pos == -1:
            return 0
        before = full_text[:pos]
        return self._count_tokens(before)

    def generate_needle_qa(self, target_tokens: int, num_needles: int = 5,
                           needle_type: str = "fact") -> Tuple[str, List[Dict], List[Dict]]:
        """
        Generate context + QA pairs.

        Returns:
            (full_context, needles, qa_pairs)
        """
        context, needles = self.generate(target_tokens, num_needles, needle_type)

        qa_pairs = []
        for n in needles:
            qa_pairs.append({
                "needle_id": n["id"],
                "question": n["query"],
                "expected": n["text"],
                "depth": n["depth"],
                "position_tokens": n.get("position_tokens", 0),
            })

        return context, needles, qa_pairs


def quick_test():
    """Demonstrate the generator."""
    gen = LongContextGenerator()

    # Generate 10K tokens with 3 fact needles
    context, needles, qa = gen.generate_needle_qa(
        target_tokens=10000,
        num_needles=3,
        needle_type="fact",
    )

    actual_tokens = len(context.split())
    print(f"=== Long-Context Generator Demo ===")
    print(f"Target tokens: 10,000")
    print(f"Actual tokens: {actual_tokens}")
    print(f"Needles: {len(needles)}")
    print(f"\nQA Pairs:")
    for q in qa:
        print(f"  {q['needle_id']} (depth={q['depth']:.0%}):")
        print(f"    Q: {q['question']}")
        print(f"    A: {q['expected'][:80]}...")

    # Show sample of the context
    print(f"\nContext preview (first 500 chars):")
    print(context[:500])
    print("...")


if __name__ == "__main__":
    quick_test()