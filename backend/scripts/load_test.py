"""Concurrent multi-user load test for general-kg-qa."""
import asyncio
import httpx
import time
import json
from dataclasses import dataclass, field

BASE_URL = "http://localhost:8000"
NUM_USERS = 20
QA_QUESTIONS = [
    "红色食品是什么？",
    "大龙湫的门票多少钱？",
    "雁荡山的主峰是什么？",
    "什么是奥林匹克精神？",
    "滴度是什么意思？",
    "灵峰在哪里？",
    "胶饴是什么？",
    "三大污染是什么？",
]


@dataclass
class Stats:
    total: int = 0
    success: int = 0
    fail: int = 0
    latencies: list = field(default_factory=list)

    def record(self, success: bool, latency: float):
        self.total += 1
        if success:
            self.success += 1
        else:
            self.fail += 1
        self.latencies.append(latency)

    def summary(self, label: str) -> str:
        if not self.latencies:
            return f"{label}: no data"
        avg = sum(self.latencies) / len(self.latencies)
        p50 = sorted(self.latencies)[len(self.latencies) // 2]
        p95 = sorted(self.latencies)[int(len(self.latencies) * 0.95)]
        p99 = sorted(self.latencies)[int(len(self.latencies) * 0.99)]
        return (
            f"{label}:\n"
            f"  Total: {self.total}  Success: {self.success}  Fail: {self.fail}\n"
            f"  Latency  avg={avg:.2f}s  p50={p50:.2f}s  p95={p95:.2f}s  p99={p99:.2f}s"
        )


async def register_user(client: httpx.AsyncClient, username: str, password: str) -> str | None:
    """Register and return token."""
    try:
        resp = await client.post("/api/v1/auth/register", json={
            "username": username,
            "email": f"{username}@test.com",
            "password": password,
        })
        if resp.status_code == 200:
            return resp.json()["access_token"]
        # Already exists, try login
        resp = await client.post("/api/v1/auth/login", json={
            "username": username,
            "password": password,
        })
        if resp.status_code == 200:
            return resp.json()["access_token"]
    except Exception:
        pass
    return None


async def user_session(
    client: httpx.AsyncClient,
    user_id: int,
    reg_stats: Stats,
    login_stats: Stats,
    qa_stats: Stats,
):
    """Simulate one user: register → login → ask questions."""
    username = f"loadtest_{user_id}"
    password = "test123456"

    # Register
    t0 = time.monotonic()
    token = await register_user(client, username, password)
    reg_stats.record(token is not None, time.monotonic() - t0)

    if not token:
        return

    headers = {"Authorization": f"Bearer {token}"}

    # Login (re-authenticate)
    t0 = time.monotonic()
    resp = await client.post("/api/v1/auth/login", json={
        "username": username, "password": password,
    }, headers=headers)
    login_stats.record(resp.status_code == 200, time.monotonic() - t0)

    # Ask questions concurrently (2 questions per user)
    questions = QA_QUESTIONS[user_id % len(QA_QUESTIONS):(user_id % len(QA_QUESTIONS)) + 2]
    for q in questions:
        t0 = time.monotonic()
        try:
            resp = await client.post("/api/v1/qa", json={"question": q}, headers=headers)
            ok = resp.status_code == 200 and resp.json().get("answer", "")
        except Exception:
            ok = False
        qa_stats.record(ok, time.monotonic() - t0)


async def main():
    print(f"=== Concurrent Load Test: {NUM_USERS} users ===\n")

    reg_stats = Stats()
    login_stats = Stats()
    qa_stats = Stats()

    limits = httpx.Limits(max_connections=50, max_keepalive_connections=20)
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0, limits=limits) as client:
        # Phase 1: All users register + login concurrently
        print(f"Phase 1: {NUM_USERS} users register + login concurrently...")
        t0 = time.monotonic()
        tasks = [
            user_session(client, i, reg_stats, login_stats, qa_stats)
            for i in range(NUM_USERS)
        ]
        await asyncio.gather(*tasks)
        total_time = time.monotonic() - t0
        print(f"  Completed in {total_time:.2f}s\n")

    # Summary
    print("=== Results ===")
    print(reg_stats.summary("Registration"))
    print(login_stats.summary("Login"))
    print(qa_stats.summary("QA"))
    print(f"\nThroughput: {qa_stats.total / total_time:.1f} QA requests/sec")


if __name__ == "__main__":
    asyncio.run(main())
