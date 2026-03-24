import asyncio
from typing import List
from .crawler import Crawler
from .governance import GovernanceNode

class HiveMindSwarm:
    def __init__(self, nodes: List[GovernanceNode]):
        self.nodes = nodes
        self.crawlers = [Crawler(node) for node in nodes]

    async def run(self):
        await asyncio.gather(*[crawler.run() for crawler in self.crawlers])

    async def distribute_tasks(self):
        while True:
            await asyncio.sleep(10)
            tasks = self.aggregate_tasks()
            await asyncio.gather(*[node.propose_tasks(tasks) for node in self.nodes])
            await asyncio.gather(*[node.vote_on_tasks() for node in self.nodes])
            approved_tasks = await self.tally_votes()
            await asyncio.gather(*[crawler.execute_tasks(approved_tasks) for crawler in self.crawlers])

    def aggregate_tasks(self) -> List[dict]:
        tasks = []
        for crawler in self.crawlers:
            tasks.extend(crawler.pending_tasks)
        return tasks

    async def tally_votes(self) -> List[dict]:
        approved_tasks = []
        for task in self.aggregate_tasks():
            if sum(node.vote_on_task(task) for node in self.nodes) > len(self.nodes) // 2:
                approved_tasks.append(task)
        return approved_tasks

if __name__ == '__main__':
    nodes = [GovernanceNode() for _ in range(5)]
    swarm = HiveMindSwarm(nodes)
    asyncio.create_task(swarm.run())
    asyncio.create_task(swarm.distribute_tasks())
    asyncio.get_event_loop().run_forever()