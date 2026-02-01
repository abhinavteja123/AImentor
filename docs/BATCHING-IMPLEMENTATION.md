# Batching Implementation for Roadmap Generation

## Problem Solved

Previously, the system attempted to generate entire roadmaps (12+ weeks with 7 days each) in a single API call, leading to:
- **JSON truncation** when responses exceeded `max_output_tokens`
- **Abandoned roadmaps** due to incomplete/invalid JSON
- **High token costs** from large single requests

## Solution: Batched Generation with Chat Sessions

### Key Components

#### 1. **LLMClient.generate_json_batched()** ([llm_client.py](../backend/app/services/ai/llm_client.py))

New method that uses Gemini's `start_chat()` feature:

```python
async def generate_json_batched(
    self,
    system_prompt: str,
    batch_prompts: List[str],
    temperature: float = 0.7,
    max_tokens: int = 8192
) -> List[Dict[str, Any]]
```

**How it works:**
1. Initializes a chat session with the model
2. Sends prompts sequentially
3. Model **remembers previous outputs** automatically
4. Returns list of parsed JSON responses

**Benefits:**
- Context maintained across batches without manual history management
- Each batch stays within token limits
- Automatic retry with fallback to extraction

#### 2. **RoadmapGenerator._generate_phase_weeks()** ([roadmap_generator.py](../backend/app/services/ai/roadmap_generator.py))

Updated to generate weeks in batches:

```python
# Generate 3 weeks at a time
batch_size = 3

for batch_start in range(start_week, end_week + 1, batch_size):
    batch_end = min(batch_start + batch_size - 1, end_week)
    
    # Include sliding window context
    context_text = self._create_sliding_window_context(all_weeks)
    
    batch_result = await self._generate_week_batch(...)
    all_weeks.extend(batch_result.get("weeks", []))
```

#### 3. **Sliding Window Context**

Each batch includes the **last 2 days** of the previous week as context:

```
Week 3: [all tasks]
  Day 6: "Build REST API endpoints"
  Day 7: "Test API with Postman" ← Included in Week 4 prompt

Week 4 Prompt:
  CONTEXT:
  Day 6: Build REST API endpoints
  Day 7: Test API with Postman
  
  Continue from here, maintaining consistency...
```

This ensures:
- Smooth progression between batches
- No duplicated content
- Consistent difficulty curve

## Architecture

### Before (Single Call)
```
User Request
    ↓
Generate Entire Roadmap (12 weeks × 7 days = 84 days)
    ↓
LLM tries to output 40,000+ tokens
    ↓
❌ Truncated at max_output_tokens (8192)
    ↓
❌ Invalid JSON → Abandoned Roadmap
```

### After (Batched)
```
User Request
    ↓
Phase 1: Weeks 1-3
    ↓
Batch 1: Weeks 1-3 (fits in 6000 tokens) ✅
    ↓
Batch 2: Weeks 4-6 (with context from Week 3) ✅
    ↓
Batch 3: Weeks 7-9 (with context from Week 6) ✅
    ↓
Batch 4: Weeks 10-12 (with context from Week 9) ✅
    ↓
✅ Complete Valid JSON Roadmap
```

## Token Efficiency

### Single Call Approach
- **Request:** ~2,000 tokens (prompt)
- **Response:** 40,000 tokens (attempted)
- **Actual:** 8,192 tokens (truncated)
- **Result:** ❌ Incomplete

### Batched Approach
- **Batch 1:** 2,000 (prompt) + 6,000 (response) = 8,000 tokens ✅
- **Batch 2:** 2,500 (prompt + context) + 6,000 (response) = 8,500 tokens ✅
- **Batch 3:** 2,500 + 6,000 = 8,500 tokens ✅
- **Batch 4:** 2,500 + 6,000 = 8,500 tokens ✅
- **Total:** ~34,000 tokens (all valid)

## Configuration

### Batch Size
```python
batch_size = 3  # weeks per batch
```

**Reasoning:**
- 3 weeks × 7 days = 21 days
- ~250 tokens per day (task details)
- 21 × 250 = ~5,250 tokens
- Leaves room for prompt (~2,000) + safety margin

### Sliding Window Size
```python
last_days = last_week.get("days", [])[-2:]  # Last 2 days
```

**Reasoning:**
- 2 days = ~500 tokens
- Provides enough context
- Minimal token overhead

## Testing

Run the test script:

```bash
cd backend
python test_batching.py
```

Expected output:
```
✅ Successfully generated 2 batches
Batch 1: 2 weeks generated
  - Week 1: Python Basics
  - Week 2: Control Flow
Batch 2: 2 weeks generated
  - Week 3: Functions
  - Week 4: Data Structures

🎉 Batching test successful!
```

## Monitoring

Check logs for batching metrics:

```python
logger.info(f"Generating batch: weeks {batch_start}-{batch_end}")
logger.info(f"Batch {i+1} response length: {len(content)} chars")
logger.info(f"Completed all {len(results)} batches successfully")
```

## Fallback Strategy

If a batch fails:
1. **Retry** with exponential backoff (tenacity decorator)
2. **Fallback** to template-based generation for that batch
3. **Continue** with next batch (doesn't fail entire roadmap)

```python
except Exception as e:
    logger.error(f"AI generation failed for weeks {batch_start}-{batch_end}")
    return self._generate_default_phase_weeks(...)
```

## Future Enhancements

1. **Adaptive Batch Size:** Adjust based on role complexity
   ```python
   batch_size = 2 if role == "AI Engineer" else 3
   ```

2. **Parallel Batch Generation:** For independent phases
   ```python
   results = await asyncio.gather(*batch_tasks)
   ```

3. **Token Usage Tracking:** Monitor and optimize
   ```python
   total_tokens = sum(batch.usage.total_tokens for batch in batches)
   ```

## Migration Notes

### Existing Code
No changes required! The batching is transparent:

```python
# This still works exactly the same
roadmap = await roadmap_generator.generate_roadmap(
    user_id=user_id,
    target_role="Full Stack Developer",
    duration_weeks=12
)
```

### Database
No schema changes needed - roadmaps are stored identically.

## Conclusion

The batching implementation solves the JSON truncation issue by:
1. ✅ Keeping each request within token limits
2. ✅ Maintaining context via chat sessions
3. ✅ Providing smooth transitions with sliding window
4. ✅ Falling back gracefully on errors
5. ✅ Zero impact on existing API contracts

This results in **100% complete roadmaps** with no abandoned generations.
