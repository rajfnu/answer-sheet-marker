#!/usr/bin/env python
"""Direct test of Ollama integration bypassing CLI"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, "src")

from answer_marker.config import settings
from answer_marker.llm.factory import create_llm_client_from_config
from answer_marker.llm.compat import LLMClientCompat


async def test_ollama():
    """Test Ollama integration directly"""
    print("="*70)
    print("Testing Ollama Integration")
    print("="*70)

    # Create LLM client
    print(f"\n1. Creating LLM client...")
    print(f"   Provider: {settings.llm_provider}")
    print(f"   Model: {settings.llm_model}")

    llm_client = create_llm_client_from_config(settings)
    client = LLMClientCompat(llm_client)

    print("   ✓ Client created successfully")

    # Test simple message
    print(f"\n2. Testing simple message...")
    response = client.messages.create(
        model="mistral",  # This will be ignored, uses configured model
        system="You are a helpful assistant.",
        messages=[{"role": "user", "content": "What is 5+5? Answer with just the number."}],
        max_tokens=100,
        temperature=0.0
    )

    print(f"   Response: {response.content[0].text}")
    print(f"   Stop reason: {response.stop_reason}")
    print(f"   ✓ Simple message test passed")

    # Test marking-related message
    print(f"\n3. Testing marking-related message...")
    response = client.messages.create(
        model="mistral",
        system="You are an expert at evaluating student answers.",
        messages=[{"role": "user", "content": "Evaluate this answer: 'The capital of France is Paris.' Is it correct? Answer yes or no."}],
        max_tokens=100,
        temperature=0.0
    )

    print(f"   Response: {response.content[0].text}")
    print(f"   ✓ Marking-related message test passed")

    print(f"\n{'='*70}")
    print("✓ All Ollama integration tests passed!")
    print("="*70)

    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_ollama())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
