import redis
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import time
import logging

class DistributedCrawler:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port)
        self.visited_key = 'visited_urls'
        self.frontier_key = 'url_frontier'
        self.logger = logging.getLogger(__name__)

    def add_url(self, url):
        """Add URL to the distributed frontier if not already visited"""
        if not self.redis_client.sismember(self.visited_key, url):
            self.redis_client.lpush(self.frontier_key, url)

    def mark_visited(self, url):
        """Mark URL as visited in distributed set"""
        self.redis_client.sadd(self.visited_key, url)

    def get_next_url(self):
        """Get next URL from distributed frontier"""
        return self.redis_client.rpop(self.frontier_key)

    def crawl(self, start_url, max_pages=100):
        """Distributed crawling with Redis-based frontier"""
        self.add_url(start_url)
        pages_crawled = 0

        while pages_crawled < max_pages:
            url = self.get_next_url()
            if not url:
                break

            url = url.decode('utf-8')
            if self.redis_client.sismember(self.visited_key, url):
                continue

            try:
                self.logger.info(f'Crawling: {url}')
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract and store content
                    title = soup.title.string if soup.title else 'No title'
                    self.redis_client.hset('page_contents', url, title)

                    # Extract and queue new links
                    for link in soup.find_all('a'):
                        href = link.get('href')
                        if href:
                            absolute_url = urljoin(url, href)
                            if absolute_url.startswith('http'):
                                self.add_url(absolute_url)

                    pages_crawled += 1
                    self.mark_visited(url)
                    
                time.sleep(1)  # Polite crawling

            except Exception as e:
                self.logger.error(f'Error crawling {url}: {str(e)}')
                continue

        return pages_crawled

    def get_stats(self):
        """Get crawler statistics"""
        return {
            'visited_urls': self.redis_client.scard(self.visited_key),
            'queued_urls': self.redis_client.llen(self.frontier_key),
            'stored_contents': self.redis_client.hlen('page_contents')
        }

    def clear_all(self):
        """Reset all crawler data"""
        self.redis_client.delete(self.visited_key)
        self.redis_client.delete(self.frontier_key)
        self.redis_client.delete('page_contents')
