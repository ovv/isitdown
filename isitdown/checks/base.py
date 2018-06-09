import attr
import logging
import asyncio

from enum import Enum

from ..notifiers import LoggingNotifier

LOG = logging.getLogger(__name__)


@attr.s
class Result:
    check = attr.ib()
    success = attr.ib()
    data = attr.ib()
    reason = attr.ib(default="")


class state(Enum):
    STOPPED = 0
    RUNNING = 1
    PAUSED = 2


class BaseChecks:
    def __init__(self, name, *, startup_delay=0, check_interval=300, notifiers=None):

        if not notifiers:
            notifiers = [
                LoggingNotifier(logger=logging.getLogger(f"isitdown.status.{name}"))
            ]

        self.name = name
        self._task = None
        self.state = state.RUNNING
        self.notifiers = notifiers
        self.startup_delay = startup_delay
        self.paused_seconds = 0
        self.check_interval = check_interval

    def start(self):
        loop = asyncio.get_event_loop()
        self._task = loop.create_task(self._start())
        return self._task

    async def _start(self):
        LOG.info(f"Starting check: {self.name}")
        try:
            await asyncio.sleep(self.startup_delay)
            await self.startup()
            while self.state in (state.RUNNING, state.PAUSED):
                if self.state == state.PAUSED:
                    await self._pause()
                else:
                    await self._run()
                    await asyncio.sleep(self.check_interval)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            LOG.exception(f"Check {self.name} crashed")
        finally:
            await self.shutdown()

    async def _run(self):
        try:
            result = await self.check()
        except Exception as e:
            LOG.debug(f"Error during check: {self.name}", exc_info=1)
            result = Result(
                check=self.name, success=False, reason=f"python exception: {e}", data=e
            )
        finally:
            if result.success:
                await self.ok(result=result)
            else:
                await self.error(result=result)

    async def _pause(self):
        if self.paused_seconds <= 0:
            self.state = state.RUNNING
        else:
            await asyncio.sleep(1)
            self.paused_seconds -= 1

    def pause(self, seconds):
        self.state = state.PAUSED
        self.paused_seconds = int(seconds)

    async def stop(self):
        self._task.cancel()
        await self._task

    async def check(self):
        LOG.debug(f"Checking with check: {self.name}")

    async def startup(self):
        pass

    async def shutdown(self):
        LOG.info(f"Shutting down check: {self.name}")
        self.running = state.STOPPED

    async def error(self, result):
        await asyncio.gather(*[notifier.error(result) for notifier in self.notifiers])

    async def ok(self, result):
        await asyncio.gather(*[notifier.ok(result) for notifier in self.notifiers])
