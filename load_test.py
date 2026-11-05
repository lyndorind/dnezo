import asyncio
import httpx
import time

URLS = [
    "http://localhost:8000/ping",
    "http://localhost:8000/status",
    "http://localhost:8000/db-test"
]

TOTAL_REQUESTS = 100
CONCURRENCY = 10

async def fetch(client, url):
    start_time = time.time()
    try:
        response = await client.get(url, timeout=5.0)
        duration = time.time() - start_time
        return response.status_code, duration
    except Exception as e:
        return 0, 0

async def bound_fetch(sem, client, url):
    async with sem:
        return await fetch(client, url)

async def main():
    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient() as client:
        tasks = []
        for _ in range(TOTAL_REQUESTS):
            url = URLS[_ % len(URLS)]
            tasks.append(bound_fetch(sem, client, url))
        
        start_total = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_total

    success = sum(1 for status, _ in results if status == 200)
    failed = len(results) - success
    print(f"--- LOAD TEST RESULTS ---")
    print(f"Total requests: {TOTAL_REQUESTS}")
    print(f"Successful: {success}")
    print(f"Failed: {failed}")
    print(f"Total time: {total_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())