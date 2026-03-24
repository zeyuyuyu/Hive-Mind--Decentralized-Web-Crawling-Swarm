import asyncio
import aiohttp
import hashlib
import time
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class CrawlResult:
    url: str
    content: str
    timestamp: float

class DistributedCrawler:
    def __init__(self, peers: List[str], blockchain_endpoint: str):
        self.peers = peers
        self.blockchain_endpoint = blockchain_endpoint
        self.crawl_results: Dict[str, CrawlResult] = {}
        self.lock = asyncio.Lock()

    async def crawl(self, url: str) -> CrawlResult:
        async with self.lock:
            if url in self.crawl_results:
                return self.crawl_results[url]

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    content = await response.text()
                    timestamp = time.time()
                    crawl_result = CrawlResult(url=url, content=content, timestamp=timestamp)
                    self.crawl_results[url] = crawl_result

                    # Broadcast the crawl result to the blockchain network
                    await self.broadcast_crawl_result(crawl_result)

                    return crawl_result

    async def broadcast_crawl_result(self, crawl_result: CrawlResult):
        payload = {
            'url': crawl_result.url,
            'content': crawl_result.content,
            'timestamp': crawl_result.timestamp,
            'hash': self.compute_hash(crawl_result)
        }

        for peer in self.peers:
            async with aiohttp.ClientSession() as session:
                await session.post(f'{peer}/crawl_result', json=payload)

        # Submit the crawl result to the blockchain
        async with aiohttp.ClientSession() as session:
            await session.post(self.blockchain_endpoint, json=payload)

    def compute_hash(self, crawl_result: CrawlResult) -> str:
        data = f'{crawl_result.url}{crawl_result.content}{crawl_result.timestamp}'.encode()
        return hashlib.sha256(data).hexdigest()
