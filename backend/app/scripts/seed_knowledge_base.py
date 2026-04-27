"""
Seed the RAG Knowledge Base with educational content.

This script directly uses the services layer (no API auth needed).
Run from the backend/ directory:

    python -m app.scripts.seed_knowledge_base

It will:
  1. Connect to the database
  2. Generate educational content for core programming topics via LLM
  3. Chunk and store them in the knowledge_documents table
"""

import asyncio
import logging
import os
import sys

# Ensure the backend package is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Topics to seed ────────────────────────────────────────────
# Each tuple: (topic, subtopic, difficulty_level)
SEED_TOPICS = [
    # Python fundamentals
    ("Python", "Variables, Data Types, and Operators", 1),
    ("Python", "Control Flow: if/elif/else and loops", 1),
    ("Python", "Functions and Scope", 2),
    ("Python", "Object-Oriented Programming: Classes and Inheritance", 3),
    ("Python", "Error Handling and Exceptions", 2),
    ("Python", "List Comprehensions and Generators", 3),
    ("Python", "Decorators and Context Managers", 4),
    ("Python", "Async/Await and Concurrency", 4),

    # Data Structures & Algorithms
    ("Data Structures", "Arrays and Linked Lists", 2),
    ("Data Structures", "Stacks, Queues, and Hash Tables", 2),
    ("Data Structures", "Trees and Binary Search Trees", 3),
    ("Data Structures", "Graphs and Graph Traversal (BFS/DFS)", 4),
    ("Algorithms", "Sorting: Bubble, Merge, Quick Sort", 3),
    ("Algorithms", "Searching: Binary Search and Two Pointers", 2),
    ("Algorithms", "Dynamic Programming Fundamentals", 4),
    ("Algorithms", "Big-O Notation and Time Complexity", 2),

    # Web Development
    ("JavaScript", "Variables, Functions, and ES6+ Features", 1),
    ("JavaScript", "Promises, Async/Await, and the Event Loop", 3),
    ("React", "Components, Props, and State", 2),
    ("React", "Hooks: useState, useEffect, useContext", 3),
    ("HTML/CSS", "Semantic HTML and Accessibility", 1),
    ("HTML/CSS", "CSS Flexbox and Grid Layout", 2),

    # Backend & Databases
    ("SQL", "SELECT, JOIN, and Subqueries", 2),
    ("SQL", "Indexing, Normalization, and Query Optimization", 3),
    ("REST APIs", "HTTP Methods, Status Codes, and REST Design", 2),
    ("REST APIs", "Authentication: JWT, OAuth, and API Security", 3),

    # DevOps & Tools
    ("Git", "Branching, Merging, and Rebasing", 2),
    ("Docker", "Containers, Images, and Docker Compose", 3),

    # System Design
    ("System Design", "Scalability, Load Balancing, and Caching", 4),
    ("System Design", "Database Sharding and Replication", 5),
]


# ── Pre-written content (no LLM needed for these) ────────────
STATIC_CONTENT = [
    {
        "topic": "Python",
        "subtopic": "Variables, Data Types, and Operators",
        "difficulty_level": 1,
        "content": """# Python Variables, Data Types, and Operators

## Variables
Variables in Python are created by assignment. No declaration needed.

```python
name = "Alice"       # str
age = 25             # int
height = 5.7         # float
is_student = True    # bool
```

## Core Data Types
| Type | Example | Mutable? |
|------|---------|----------|
| int | 42 | No |
| float | 3.14 | No |
| str | "hello" | No |
| bool | True/False | No |
| list | [1, 2, 3] | Yes |
| tuple | (1, 2, 3) | No |
| dict | {"a": 1} | Yes |
| set | {1, 2, 3} | Yes |

## Type Checking
```python
type(42)          # <class 'int'>
isinstance(42, int)  # True
```

## Operators
- Arithmetic: `+`, `-`, `*`, `/`, `//` (floor), `%` (mod), `**` (power)
- Comparison: `==`, `!=`, `<`, `>`, `<=`, `>=`
- Logical: `and`, `or`, `not`
- Assignment: `=`, `+=`, `-=`, `*=`
- Identity: `is`, `is not`
- Membership: `in`, `not in`

## Common Mistakes
1. Using `=` instead of `==` for comparison
2. Confusing mutable vs immutable types
3. Integer division: `7/2 = 3.5` but `7//2 = 3`
""",
    },
    {
        "topic": "Data Structures",
        "subtopic": "Arrays and Linked Lists",
        "difficulty_level": 2,
        "content": """# Arrays and Linked Lists

## Arrays (Python Lists)
Arrays store elements in contiguous memory locations.

```python
arr = [10, 20, 30, 40, 50]
arr[0]       # 10 — O(1) access
arr.append(60)  # O(1) amortized
arr.insert(2, 25)  # O(n) — shifts elements
```

### Time Complexities
| Operation | Time |
|-----------|------|
| Access by index | O(1) |
| Search | O(n) |
| Insert at end | O(1) amortized |
| Insert at position | O(n) |
| Delete | O(n) |

## Linked Lists
Each node stores data + pointer to next node.

```python
class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None

    def append(self, data):
        new_node = Node(data)
        if not self.head:
            self.head = new_node
            return
        current = self.head
        while current.next:
            current = current.next
        current.next = new_node
```

### When to Use What
- **Array**: Random access needed, known size, cache-friendly
- **Linked List**: Frequent insertions/deletions, unknown size, no random access needed

## Key Differences
| Feature | Array | Linked List |
|---------|-------|-------------|
| Access | O(1) | O(n) |
| Insert (beginning) | O(n) | O(1) |
| Memory | Contiguous | Scattered |
| Cache performance | Better | Worse |
""",
    },
    {
        "topic": "Algorithms",
        "subtopic": "Big-O Notation and Time Complexity",
        "difficulty_level": 2,
        "content": """# Big-O Notation and Time Complexity

## What is Big-O?
Big-O describes the upper bound of an algorithm's growth rate.
It tells you how performance scales with input size.

## Common Complexities (fastest to slowest)
| Big-O | Name | Example |
|-------|------|---------|
| O(1) | Constant | Array access, hash lookup |
| O(log n) | Logarithmic | Binary search |
| O(n) | Linear | Linear search, single loop |
| O(n log n) | Linearithmic | Merge sort, quick sort (avg) |
| O(n²) | Quadratic | Nested loops, bubble sort |
| O(2^n) | Exponential | Recursive Fibonacci |
| O(n!) | Factorial | Permutations |

## How to Analyze
```python
# O(1) - constant
def get_first(arr):
    return arr[0]

# O(n) - linear
def find_max(arr):
    max_val = arr[0]
    for x in arr:        # n iterations
        if x > max_val:
            max_val = x
    return max_val

# O(n²) - quadratic
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):       # n iterations
        for j in range(n-1): # n iterations each
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]

# O(log n) - logarithmic
def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:          # halves each time
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
```

## Rules for Big-O
1. Drop constants: O(2n) → O(n)
2. Drop lower-order terms: O(n² + n) → O(n²)
3. Different inputs = different variables: O(a + b), not O(n)
4. Nested loops multiply: O(n) × O(n) = O(n²)
""",
    },
]


async def seed():
    """Main seed function."""
    # Import inside function to avoid circular imports
    from app.database.postgres import AsyncSessionLocal
    from app.services.ai.rag.knowledge_base import KnowledgeBase

    logger.info("=" * 60)
    logger.info("  AgentRAG-Tutor Knowledge Base Seeder")
    logger.info("=" * 60)

    async with AsyncSessionLocal() as db:
        kb = KnowledgeBase(db)

        # Check current state
        stats = await kb.get_stats()
        logger.info("Current KB: %d chunks, %d topics", stats["total_chunks"], stats["topics_count"])

        if stats["total_chunks"] > 0:
            logger.info("Knowledge base already has content. Skipping static seed.")
        else:
            # Phase 1: Insert static content (instant, no LLM needed)
            logger.info("\n--- Phase 1: Inserting static content ---")
            for item in STATIC_CONTENT:
                docs = await kb.ingest_document(
                    topic=item["topic"],
                    content=item["content"],
                    subtopic=item.get("subtopic"),
                    difficulty_level=item.get("difficulty_level", 1),
                    source="static-seed",
                )
                logger.info("  ✓ %s / %s → %d chunks", item["topic"], item.get("subtopic", ""), len(docs))
            await db.commit()

        # Phase 2: Generate content via LLM for remaining topics
        existing_topics = set(await kb.get_topics())
        remaining = [(t, s, d) for t, s, d in SEED_TOPICS
                     if t not in existing_topics or True]  # always check subtopics

        logger.info("\n--- Phase 2: LLM-generated content (%d topics) ---", len(remaining))
        logger.info("This uses your LLM providers and may take a few minutes.\n")

        generated = 0
        errors = 0
        for topic, subtopic, difficulty in remaining:
            try:
                logger.info("  Generating: %s / %s (difficulty=%d)...", topic, subtopic, difficulty)
                content = await kb.generate_content_for_topic(topic, subtopic, difficulty)
                docs = await kb.ingest_document(
                    topic=topic,
                    content=content,
                    subtopic=subtopic,
                    difficulty_level=difficulty,
                    source="llm-generated",
                    metadata={"generator": "seed_script"},
                )
                await db.commit()
                logger.info("    ✓ Ingested %d chunks", len(docs))
                generated += 1
            except Exception as e:
                logger.error("    ✗ Failed: %s", e)
                errors += 1
                continue

        # Final stats
        final_stats = await kb.get_stats()
        logger.info("\n" + "=" * 60)
        logger.info("  Seeding complete!")
        logger.info("  Total chunks: %d", final_stats["total_chunks"])
        logger.info("  Total topics: %d", final_stats["topics_count"])
        logger.info("  Generated: %d | Errors: %d", generated, errors)
        logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
