"""Integration test for HuggingFace agent with DeepScaleR-1.5B-Preview model."""

import asyncio

from midori_ai_agent_base import AgentPayload
from midori_ai_agent_huggingface import HuggingFaceLocalAgent


async def main() -> None:
    """Run integration test for HuggingFace agent."""
    print("Starting HuggingFace agent integration test...")
    print("Creating agent with model: agentica-org/DeepScaleR-1.5B-Preview")
    agent = HuggingFaceLocalAgent(model="agentica-org/DeepScaleR-1.5B-Preview", max_new_tokens=50, temperature=0.7, trust_remote_code=True)
    try:
        print("Creating test payload...")
        payload = AgentPayload(user_message="What is 2+2?", thinking_blob="", system_context="You are a helpful assistant.", user_profile={}, tools_available=[], session_id="integration-test")
        print("Invoking agent (this will download and load the model on first run)...")
        response = await agent.invoke(payload)
        print(f"Response received: {response.response}")
        assert response.response, "Response should not be empty"
        assert isinstance(response.response, str), "Response should be a string"
        print("✓ Agent invocation successful")
        print("✓ Response is valid")
        print("✓ Pipeline loaded successfully")
        print("\nIntegration test PASSED!")
    finally:
        print("Cleaning up (unloading model)...")
        await agent.unload_model()
        print("✓ Model unloaded successfully")


if __name__ == "__main__":
    asyncio.run(main())
