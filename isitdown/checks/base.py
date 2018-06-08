import attr
import logging
import asyncio

from ..notifiers import LoggingNotifier

LOG = logging.getLogger(__name__)


@attr.s
class Result:
    check = attr.ib()
    success = attr.ib()
    data = attr.ib()
    reason = attr.ib(default="")


class BaseChecks:
    def __init__(self, name, *, startup_delay=0, check_interval=300, notifiers=None):
        self.name = name
        self.running = True
        self.check_interval = check_interval
        self.startup_delay = startup_delay

        if not notifiers:
            notifiers = [
                LoggingNotifier(
                    logger=logging.getLogger(f"isitdown.status.{self.name}")
                )
            ]
        self.notifiers = notifiers

    async def start(self):
        LOG.info(f"Starting check: {self.name}")
        try:
            await self.startup()
            await asyncio.sleep(self.startup_delay)
            while self.running:
                try:
                    result = await self.check()
                except Exception as e:
                    LOG.debug(f"Error during check: {self.name}", exc_info=1)
                    result = Result(
                        check=self.name,
                        success=False,
                        reason=f"python exception: {e}",
                        data=e,
                    )
                finally:
                    if result.success:
                        await self.ok(result=result)
                    else:
                        await self.error(result=result)
                await asyncio.sleep(self.check_interval)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            LOG.exception(f"Check {self.name} crashed")
        finally:
            await self.shutdown()

    async def check(self):
        LOG.debug(f"Checking with check: {self.name}")

    async def startup(self):
        pass

    async def shutdown(self):
        LOG.info(f"Shutting down check: {self.name}")
        self.running = False

    async def error(self, result):
        await asyncio.gather(*[notifier.error(result) for notifier in self.notifiers])

    async def ok(self, result):
        await asyncio.gather(*[notifier.ok(result) for notifier in self.notifiers])
