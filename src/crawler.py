import asyncio
from urllib.parse import urlparse
import aiohttp
import time
from collections import defaultdict

class DistributedCrawler:
    def __init__(self, max_concurrent=10):
        self.max_concurrent = max_concurrent
        self.seen_urls = set()
        self.queue = asyncio.Queue()
        self.domain_timestamps = defaultdict(list)
        self.domain_delay = 1.0  # Minimum delay between requests to same domain
        self.session = None

    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session:
            await self.session.close()

    def can_crawl_domain(self, domain):
        """Rate limiting check for domain"""
        now = time.time()
        timestamps = self.domain_timestamps[domain]
        
        # Clean old timestamps
        while timestamps and timestamps[0] < now - 60:
            timestamps.pop(0)
            
        # Check if enough time passed since last request
        if timestamps and (now - timestamps[-1]) < self.domain_delay:
            return False
            
        return len(timestamps) < 60  # Max 60 requests per minute per domain

    async def add_url(self, url):
        if url not in self.seen_urls:
            self.seen_urls.add(url)
            await self.queue.put(url)

    async def crawl_url(self, url):
        """Crawl a single URL with rate limiting"""
        domain = urlparse(url).netloc
        
        if not self.can_crawl_domain(domain):
            # Re-queue for later if rate limited
            await self.queue.put(url)
            return None

        try:
            await self.init_session()
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    self.domain_timestamps[domain].append(time.time())
                    return content
        except Exception as e:
            print(f"Error crawling {url}: {str(e)}")
        return None

    async def worker(self):
        """Worker process that continuously pulls from queue"""
        while True:
            url = await self.queue.get()
            try:
                content = await self.crawl_url(url)
                if content:
                    # Process content here
                    print(f"Successfully crawled: {url}")
            finally:
                self.queue.task_done()

    async def run(self, seed_urls):
        """Main crawler entry point"""
        # Add seed URLs to queue
        for url in seed_urls:
            await self.add_url(url)

        # Start workers
        workers = []
        for _ in range(self.max_concurrent):
            worker = asyncio.create_task(self.worker())
            workers.append(worker)

        # Wait for queue to be fully processed
        await self.queue.join()

        # Cancel workers
        for worker in workers:
            worker.cancel()

        # Cleanup
        await self.close()

if __name__ == "__main__":
    # Example usage
    crawler = DistributedCrawler(max_concurrent=5)
    seed_urls = [
        "http://example.com\