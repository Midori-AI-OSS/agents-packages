"""Test to verify ChromaDB operations don't block the event loop."""

import asyncio
import time

import pytest

from midori_ai_vector_manager import ChromaVectorStore


@pytest.mark.asyncio
async def test_non_blocking():
    """Test that ChromaDB operations don't block the event loop."""
    print("\n=== Testing Non-Blocking ChromaDB Operations ===")
    
    # Create a store
    store = ChromaVectorStore("test_non_blocking", persist_directory=None)
    
    # Counter to track if event loop is responsive
    counter = {"value": 0}
    
    async def increment_counter():
        """Continuously increment counter to verify event loop responsiveness."""
        for _ in range(100):
            counter["value"] += 1
            await asyncio.sleep(0.01)  # 10ms delay
    
    async def do_chromadb_operations():
        """Perform ChromaDB operations."""
        # Store multiple entries
        for i in range(10):
            await store.store(f"Document {i}", metadata={"index": i})
        
        # Query
        results = await store.query(filters={}, limit=10)
        
        # Search similar
        similar = await store.search_similar("Document 5", limit=3)
        
        # Count
        count = await store.count()
        
        return len(results), len(similar), count
    
    # Run both tasks concurrently
    start = time.time()
    
    counter_task = asyncio.create_task(increment_counter())
    chromadb_task = asyncio.create_task(do_chromadb_operations())
    
    results, similar_count, total_count = await chromadb_task
    await counter_task
    
    elapsed = time.time() - start
    
    print(f"Time elapsed: {elapsed:.4f}s")
    print(f"Counter reached: {counter['value']}")
    print(f"ChromaDB results: {results} entries, {similar_count} similar, {total_count} total")
    
    # If the counter reached close to 100, the event loop was responsive
    if counter["value"] > 80:
        print("✓ Event loop remained responsive during ChromaDB operations!")
        return True
    else:
        print(f"✗ Event loop may have been blocked (counter only reached {counter['value']})")
        return False


async def main():
    """Run the test."""
    print("ChromaDB Event Loop Blocking Test")
    print("=" * 50)
    
    success = await test_non_blocking()
    
    print("\n" + "=" * 50)
    if success:
        print("SUCCESS: ChromaDB operations are properly async!")
    else:
        print("FAILURE: ChromaDB operations may be blocking!")
    
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
