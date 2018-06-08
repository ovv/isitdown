import asyncio
import logging
import aiohttp.web

LOG = logging.getLogger(__name__)


class isitdown(aiohttp.web.Application):
    def __init__(self, *checks, **kwargs):
        super().__init__(**kwargs)
        if checks is None:
            checks = dict()

        self.checks = checks
        self._checks = dict()

        self.on_startup.append(self._start_checks)
        self.on_shutdown.append(self._cleanup_checks)

    def start(self, **kwargs):
        LOG.info("Starting isitdown")
        aiohttp.web.run_app(self, **kwargs)

    async def _start_checks(self, isitdown):
        for check in self.checks:
            self._checks[check] = self.loop.create_task(check.start())

    async def _cleanup_checks(self, isitdown):
        for task in self._checks.values():
            task.cancel()
        await asyncio.gather(*self._checks.values())
