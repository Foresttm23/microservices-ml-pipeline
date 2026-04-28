import asyncio
import os

from shared.messaging import RedisClient


async def main() -> None:
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        print("Set REDIS_URL to run the Redis smoke example.")
        return

    client = RedisClient(redis_url, decode_responses=True)
    await client.task_queue.enqueue("ping")
    message = await client.task_queue.dequeue(timeout=1)
    print(f"Queue message: {message}")

    channel = client.results_pubsub.channel_for("demo")
    await client.results_pubsub.publish(channel, "hello")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
