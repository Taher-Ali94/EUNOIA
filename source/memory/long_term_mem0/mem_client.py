from ...config.mem0_config import config
from mem0 import Memory
import asyncio
from typing import Optional, Dict, List
import time


class MemoryClient:
    def __init__(self, user_id: str = "default_user"):
        self.memory: Optional[Memory] = None
        self.user_id = user_id
        self.add_queue = asyncio.Queue()
        self.search_queue = asyncio.Queue()
        self.result_cache = {}
        self.add_worker_task = None
        self.search_worker_task = None

    def initialize_memory_sync(self):
        try:
            self.memory = Memory.from_config(config)
        except Exception as e:
            print(f"Error initializing memory: {e}")
            self.memory = None
            raise

    async def initialize_memory(self):
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.initialize_memory_sync)
        except Exception as e:
            print(f"Error initializing memory: {e}")
            self.memory = None
            return

        if self.memory is None:
            print("Memory failed to initialize")
            return

        try:
            if self.add_worker_task is not None:
                return

            self.add_worker_task = asyncio.create_task(self.add_worker())
            self.search_worker_task = asyncio.create_task(self.search_worker())

        except Exception as e:
            print(f"Error starting workers: {e}")

    async def add_memory(self, messages: List[Dict[str, str]]) -> None:
        if self.memory is None:
            print("Memory not initialized")
            return

        task_id = f"add_{time.time()}_{self.user_id}"

        task = {
            "task_id": task_id,
            "messages": messages,
        }

        await self.add_queue.put(task)

    async def search_memory(self, query: str, limit: int = 5) -> List[Dict]:
        if self.memory is None:
            print("Memory not initialized")
            return []

        task_id = f"search_{time.time()}_{self.user_id}"

        task = {
            "task_id": task_id,
            "query": query,
            "limit": limit,
        }

        await self.search_queue.put(task)
        print(f"🔍 Search queued: {query}")

        while True:
            if task_id in self.result_cache:
                result = self.result_cache.pop(task_id)

                if result.get("status") == "success":
                    return result.get("results", [])
                else:
                    print(f"Error in search: {result.get('error')}")
                    return []

            await asyncio.sleep(0.05)

    async def add_worker(self):

        try:
            while True:
                task = await self.add_queue.get()

                if task is None:
                    break

                try:
                    loop = asyncio.get_running_loop()

                    await loop.run_in_executor(
                        None,
                        self._add_memory_sync,
                        task["messages"],
                    )
                except Exception as e:
                    print(f" Error adding memory: {e}")

                finally:
                    self.add_queue.task_done()

        except asyncio.CancelledError:
            print("Add worker cancelled")

    def _add_memory_sync(self, messages: List[Dict[str, str]]) -> None:
        self.memory.add(
            messages=messages,
            user_id=self.user_id,
        )

    async def search_worker(self):
        try:
            while True:
                task = await self.search_queue.get()

                if task is None:
                    break

                task_id = task["task_id"]

                try:
                    loop = asyncio.get_running_loop()

                    results = await loop.run_in_executor(
                        None,
                        self._search_memory_sync,
                        task["query"],
                        task["limit"],
                    )


                    self.result_cache[task_id] = {
                        "status": "success",
                        "results": results,
                    }

                except Exception as e:
                    print(f"Error searching memory: {e}")
                    self.result_cache[task_id] = {
                        "status": "error",
                        "error": str(e),
                    }

                finally:
                    self.search_queue.task_done()

        except asyncio.CancelledError:
            print(" Search worker cancelled")

    def _search_memory_sync(self, query: str, limit: int) -> List[Dict]:
        return self.memory.search(
            query=query,
            filters={"user_id": self.user_id},
            limit=limit,
        )

    async def stop(self) -> None:

        await self.add_queue.join()
        await self.search_queue.join()

        await self.add_queue.put(None)
        await self.search_queue.put(None)

        if self.add_worker_task:
            self.add_worker_task.cancel()
            try:
                await self.add_worker_task
            except asyncio.CancelledError:
                pass

        if self.search_worker_task:
            self.search_worker_task.cancel()
            try:
                await self.search_worker_task
            except asyncio.CancelledError:
                pass
