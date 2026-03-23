import os
import asyncio
import logging
from .agent import Agent
from .swarm import Swarm
from .governance import GovernanceProtocol

logging.basicConfig(level=logging.INFO)

async def main():
    """Main entry point for the Hive-Mind application."""
    governance_protocol = GovernanceProtocol()
    swarm = Swarm(governance_protocol)
    
    # Spawn and initialize agents
    for _ in range(100):
        agent = Agent(swarm)
        await agent.start()

    # Run the swarm indefinitely
    await swarm.run()

if __name__ == "__main__":
    asyncio.run(main())