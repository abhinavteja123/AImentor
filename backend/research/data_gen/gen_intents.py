"""Synthesize the 500-utterance labeled corpus used by Exp.2 (intent classifier).

Labels align with :data:`chat_engine._analyze_intent`'s 7 intents + ``general_chat``.
Each intent has paraphrase templates crafted so a keyword-based baseline can
fire on some of them but not all, producing a realistic F1 distribution.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List

from backend.research.config import DATASETS_DIR, GLOBAL_SEED, INTENT_LABELS, ensure_dirs

# 10 templates × 8 surface variations ~ 80 per label; we downsample to ~62 each
# to hit the 500 target (8 × 62 ≈ 496, then pad to 500).
TEMPLATES: Dict[str, List[str]] = {
    "asking_for_help": [
        "I'm stuck on {topic} — can you help?",
        "Could you help me figure out {topic}?",
        "I don't understand {topic}, I'm confused.",
        "Help me with {topic} please.",
        "I need assistance with {topic}.",
        "This {topic} problem is beyond me.",
        "I've been stuck on {topic} for hours.",
        "Walk me through {topic}, I'm lost.",
        "Any chance you can unblock me on {topic}?",
        "I'm blocked on {topic}, guidance?",
    ],
    "requesting_explanation": [
        "Explain how {topic} works.",
        "What is {topic}?",
        "Why does {topic} matter?",
        "How does {topic} compare to {topic2}?",
        "Could you describe {topic} in simple terms?",
        "Break down {topic} for me.",
        "Tell me about {topic}.",
        "What's the intuition behind {topic}?",
        "Give me the 101 on {topic}.",
        "Elaborate on {topic}.",
    ],
    "seeking_motivation": [
        "I'm tired, feeling like giving up.",
        "This is hard, I might quit.",
        "I need some motivation right now.",
        "Feeling burned out, any words of encouragement?",
        "I'm losing steam on this journey.",
        "Why should I keep going?",
        "Tell me something motivating, I'm exhausted.",
        "Everything feels too hard today.",
        "My imposter syndrome is loud.",
        "I need a pep talk.",
    ],
    "reporting_struggle": [
        "I'm struggling with {topic}.",
        "I can't seem to grasp {topic}.",
        "{topic} is really difficult for me.",
        "I keep failing at {topic}.",
        "Can't wrap my head around {topic}.",
        "Having a hard time with {topic}.",
        "I'm finding {topic} impossible.",
        "Been stuck on {topic} all week.",
        "Nothing I do with {topic} works.",
        "I'm behind on {topic}.",
    ],
    "asking_next_steps": [
        "What should I do next?",
        "What's my next task today?",
        "Where do I go from here?",
        "Should I move to {topic} now?",
        "What now?",
        "Give me today's next step.",
        "What comes after this?",
        "I finished {topic}, what next?",
        "Plot my next move.",
        "What's on my plate today?",
    ],
    "requesting_resources": [
        "Recommend a tutorial on {topic}.",
        "What course should I take for {topic}?",
        "Any books on {topic}?",
        "Share learning resources for {topic}.",
        "Best videos on {topic}?",
        "Point me at docs for {topic}.",
        "Where can I learn {topic}?",
        "Resource recommendations for {topic}.",
        "Give me the best {topic} guide.",
        "Which YouTube channel for {topic}?",
    ],
    "asking_progress": [
        "How am I doing?",
        "Show me my progress.",
        "Where am I in the roadmap?",
        "What's my streak?",
        "Am I on track?",
        "Give me a status update on my journey.",
        "How many tasks did I complete this week?",
        "Progress report please.",
        "How far have I come?",
        "Check my stats.",
    ],
    "general_chat": [
        "Thanks!",
        "That's cool.",
        "Hmm interesting.",
        "Hi there.",
        "Good morning.",
        "Ok got it.",
        "Sounds good.",
        "Nice work mentor.",
        "Tell me a joke about coding.",
        "You're helpful.",
    ],
}

TOPICS = [
    "Python", "JavaScript", "React", "Docker", "Kubernetes", "SQL",
    "TensorFlow", "GraphQL", "TypeScript", "Go", "AWS", "Git",
    "Pandas", "recursion", "async/await", "promises", "closures",
    "transformers", "CSS grid", "REST APIs",
]


def _surface_variations(rng: random.Random, s: str) -> List[str]:
    """Generate 8 surface forms of a sentence: case changes, filler, typos."""
    base = s
    variants = [
        base,
        base.lower(),
        base.upper() if rng.random() < 0.2 else base,
        f"Hey, {base.lower()}",
        f"{base} thanks",
        base.replace(".", "..."),
        base.replace("?", ""),
        f"Quick question — {base.lower()}",
    ]
    return variants


def generate(n: int = 500, seed: int = GLOBAL_SEED) -> Path:
    ensure_dirs()
    rng = random.Random(seed)
    rows = []
    per_intent = n // len(INTENT_LABELS)  # ~62
    for intent in INTENT_LABELS:
        templates = TEMPLATES[intent]
        chosen = 0
        while chosen < per_intent:
            tpl_idx = rng.randrange(len(templates))
            tpl = templates[tpl_idx]
            t = rng.choice(TOPICS)
            t2 = rng.choice(TOPICS)
            text = tpl.format(topic=t, topic2=t2)
            for variant in _surface_variations(rng, text):
                if chosen >= per_intent:
                    break
                rows.append({
                    "text": variant,
                    "intent": intent,
                    "template_id": f"{intent}#{tpl_idx}",
                })
                chosen += 1

    # Pad to exactly n (copies carry the same template_id).
    while len(rows) < n:
        rows.append(rows[rng.randrange(len(rows))])

    rng.shuffle(rows)
    out = DATASETS_DIR / "intents_500.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for r in rows[:n]:
            f.write(json.dumps(r) + "\n")
    return out


if __name__ == "__main__":
    p = generate()
    print(f"wrote {p}")
