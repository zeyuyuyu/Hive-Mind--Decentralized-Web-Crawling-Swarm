import multiprocessing as mp
import requests
from bs4 import BeautifulSoup

class WebCrawler:
    def __init__(self, start_urls, num_workers):
        self.start_urls = start_urls
        self.num_workers = num_workers
        self.task_queue = mp.Queue()
        self.result_queue = mp.Queue()
        self.visited_urls = set()

    def _worker(self):
        while True:
            try:
                url = self.task_queue.get(timeout=1)
            except:
                break

            try:
                response = requests.get(url)
                soup = BeautifulSoup(response.content, 'html.parser')
                links = [link.get('href') for link in soup.find_all('a')]
                self.result_queue.put((url, links))
                self.visited_urls.add(url)
            except:
                self.result_queue.put((url, []))

    def crawl(self):
        for url in self.start_urls:
            self.task_queue.put(url)

        workers = [mp.Process(target=self._worker) for _ in range(self.num_workers)]
        for worker in workers:
            worker.start()

        results = []
        while len(results) < len(self.start_urls):
            try:
                results.append(self.result_queue.get(timeout=1))
            except:
                pass

        for worker in workers:
            worker.terminate()

        return results

if __name__ == '__main__':
    start_urls = ['https://www.example.com', 'https://www.google.com', 'https://www.github.com']
    crawler = WebCrawler(start_urls, num_workers=4)
    results = crawler.crawl()
    for url, links in results:
        print(f'URL: {url}')
        print(f'Links: {links}')
