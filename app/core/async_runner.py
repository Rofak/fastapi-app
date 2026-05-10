import asyncio


class AsyncRunner:

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def run(self, coro):
        return self.loop.run_until_complete(coro)


runner = AsyncRunner()