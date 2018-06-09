import asyncio
import logging
import functools
import aiohttp.web

LOG = logging.getLogger(__name__)


class IsItDown(aiohttp.web.Application):
    def __init__(self, *checks, **kwargs):
        super().__init__(**kwargs)
        if checks is None:
            checks = list()

        self.checks = dict()
        self.on_startup.append(functools.partial(self._start_checks, checks))
        self.on_shutdown.append(self._cleanup_checks)

    def start(self, **kwargs):
        LOG.info("Starting isitdown")
        aiohttp.web.run_app(self, **kwargs)

    async def _start_checks(self, checks, app):
        for check in checks:
            if check.name in self.checks:
                raise RuntimeError(f"Duplicated check name: {check.name}")

            self.checks[check.name] = check
            check.start()

    async def _cleanup_checks(self, app):
        tasks = [check.stop() for check in self.checks.values()]
        await asyncio.gather(*tasks)
