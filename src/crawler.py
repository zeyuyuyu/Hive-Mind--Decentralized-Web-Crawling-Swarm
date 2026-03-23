import mmh3
from bitarray import bitarray
from typing import List, Set
from urllib.parse import urlparse
import redis

class DistributedFrontier:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis = redis.Redis(host=redis_host, port=redis_port)
        self.bloom_filter = BloomFilter(capacity=10000000, error_rate=0.01)
    
    def add_urls(self, urls: List[str]) -> None:
        """Add new URLs to the distributed frontier"""
        for url in urls:
            if not self.bloom_filter.contains(url):
                self.bloom_filter.add(url)
                normalized_url = self._normalize_url(url)
                domain = urlparse(normalized_url).netloc
                self.redis.lpush(f'frontier:{domain}', normalized_url)
    
    def get_next_urls(self, batch_size: int = 100) -> List[str]:
        """Get next batch of URLs to crawl, balanced across domains"""
        domains = self.redis.keys('frontier:*')
        if not domains:
            return []
        
        urls = []
        urls_per_domain = max(1, batch_size // len(domains))
        
        for domain in domains:
            domain_urls = self.redis.lrange(domain, 0, urls_per_domain - 1)
            self.redis.ltrim(domain, urls_per_domain, -1)
            urls.extend([url.decode() for url in domain_urls])
        
        return urls[:batch_size]
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL to avoid duplicates"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

class BloomFilter:
    def __init__(self, capacity: int, error_rate: float):
        """Initialize Bloom Filter with given capacity and error rate"""
        self.size = self._get_size(capacity, error_rate)
        self.hash_count = self._get_hash_count(self.size, capacity)
        self.bit_array = bitarray(self.size)
        self.bit_array.setall(0)
    
    def add(self, item: str) -> None:
        """Add an item to the Bloom Filter"""
        for seed in range(self.hash_count):
            index = mmh3.hash(item, seed) % self.size
            self.bit_array[index] = 1
    
    def contains(self, item: str) -> bool:
        """Check if an item might be in the Bloom Filter"""
        for seed in range(self.hash_count):
            index = mmh3.hash(item, seed) % self.size
            if not self.bit_array[index]:
                return False
        return True
    
    @staticmethod
    def _get_size(capacity: int, error_rate: float) -> int:
        """Calculate optimal bit array size"""
        return int(-capacity * math.log(error_rate) / (math.log(2) ** 2))
    
    @staticmethod
    def _get_hash_count(size: int, capacity: int) -> int:
        """Calculate optimal number of hash functions"""
        return int(size / capacity * math.log(2))
