"""
Test script to demonstrate the batching technique for roadmap generation.
This shows how the system now generates roadmaps in smaller batches to avoid JSON truncation.
"""

import asyncio
import logging
from app.services.ai.llm_client import get_llm_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_batched_generation():
    """Test the new batched JSON generation method."""
    
    llm = get_llm_client()
    
    # Example: Generate a simple curriculum in 2 batches
    system_prompt = """You are a Python programming instructor.
Generate structured learning content in valid JSON format."""

    # Batch 1: Weeks 1-2
    batch_1_prompt = """Generate weeks 1-2 of a Python beginner course.

Return JSON with this structure:
{
  "weeks": [
    {
      "week_number": 1,
      "topic": "Python Basics",
      "tasks": ["Install Python", "Hello World", "Variables"]
    }
  ]
}

Generate 2 weeks."""

    # Batch 2: Weeks 3-4 (with context from batch 1)
    batch_2_prompt = """Continue from Week 2 which covered basic syntax.

Now generate weeks 3-4 focusing on more advanced topics.

Return JSON with the same structure as before.
Generate 2 weeks (weeks 3-4)."""

    try:
        logger.info("Starting batched generation test...")
        
        # Generate in batches using chat session
        results = await llm.generate_json_batched(
            system_prompt=system_prompt,
            batch_prompts=[batch_1_prompt, batch_2_prompt],
            temperature=0.7,
            max_tokens=4096
        )
        
        logger.info(f"✅ Successfully generated {len(results)} batches")
        
        for i, batch_result in enumerate(results, 1):
            weeks = batch_result.get("weeks", [])
            logger.info(f"Batch {i}: {len(weeks)} weeks generated")
            for week in weeks:
                logger.info(f"  - Week {week.get('week_number')}: {week.get('topic')}")
        
        logger.info("\n🎉 Batching test successful!")
        logger.info("This technique prevents JSON truncation by:")
        logger.info("  1. Generating 3 weeks at a time (smaller token size)")
        logger.info("  2. Using chat sessions to maintain context")
        logger.info("  3. Including sliding window (last 2 days) as context")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        return False


async def main():
    """Run the test."""
    success = await test_batched_generation()
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
