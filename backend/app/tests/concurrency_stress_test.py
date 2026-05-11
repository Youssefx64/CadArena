import asyncio
import httpx
import time
import random
import statistics
from uuid import uuid4

BASE_URL = "http://localhost:8000/api/v1"
CONCURRENCY = 20
TOTAL_REQUESTS = 100

async def send_request(client, user_id, project_id):
    start = time.perf_counter()
    prompt = f"Concurrency test prompt {uuid4().hex[:6]}"
    try:
        # Using the iterate endpoint as it's a good representative of the pipeline
        resp = await client.post(
            f"/workspace/{project_id}/iterate",
            json={
                "user_id": user_id,
                "prompt": prompt,
                "current_layout": None,
                "model": "baseline"
            },
            timeout=120.0
        )
        latency = (time.perf_counter() - start) * 1000
        return resp.status_code, latency
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return str(e), latency

async def main():
    user_id = f"tester_{uuid4().hex[:6]}"
    project_name = f"StressTest_{int(time.time())}"
    
    async with httpx.AsyncClient(timeout=10.0) as setup_client:
        # 1. Create project
        resp = await setup_client.post(
            f"{BASE_URL}/workspace/projects",
            json={"user_id": user_id, "name": project_name}
        )
        project_id = resp.json()["id"]
        print(f"Created project {project_id} for user {user_id}")

    latencies = []
    status_codes = {}

    print(f"Starting stress test: {TOTAL_REQUESTS} requests, concurrency={CONCURRENCY}...")
    
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Semaphore to control concurrency
        sem = asyncio.Semaphore(CONCURRENCY)
        
        async def sem_request():
            async with sem:
                return await send_request(client, user_id, project_id)

        tasks = [sem_request() for _ in range(TOTAL_REQUESTS)]
        results = await asyncio.gather(*tasks)

        for status, latency in results:
            latencies.append(latency)
            status_codes[status] = status_codes.get(status, 0) + 1

    print("\n--- STRESS TEST RESULTS ---")
    print(f"Total Requests: {TOTAL_REQUESTS}")
    print(f"Status Codes: {status_codes}")
    if latencies:
        print(f"Avg Latency: {statistics.mean(latencies):.2f}ms")
        print(f"Min Latency: {min(latencies):.2f}ms")
        print(f"Max Latency: {max(latencies):.2f}ms")
        print(f"P95 Latency: {statistics.quantiles(latencies, n=20)[18]:.2f}ms")

if __name__ == "__main__":
    asyncio.run(main())
