import attr
import logging

from enum import Enum

LOG = logging.getLogger(__name__)


class State(Enum):
    OK = 0
    ERROR = 1


class BaseNotifier:
    def __init__(self, notify_after=1):
        self.errors = 0
        self.state = State.OK
        self.notify_after = notify_after

    async def error(self, result):
        self.state = State.ERROR
        self.errors += 1
        if self.errors % self.notify_after == 0:
            await self._error(result)
        else:
            await self._silenced_error(result)

    async def ok(self, result):
        if self.state == State.ERROR:
            self.state = State.OK
            await self._recover(result)
        else:
            await self._ok(result)

    async def _error(self, result):
        raise NotImplementedError()

    async def _ok(self, result):
        raise NotImplementedError()

    async def _recover(self, result):
        raise NotImplementedError()

    async def _silenced_error(self, result):
        pass


class LoggingNotifier(BaseNotifier):
    def __init__(self, *, logger=None, **kwargs):
        super().__init__(**kwargs)

        if not logger:
            logger = logging.getLogger("isitdown.status")

        self.logger = logger

    async def _error(self, result):
        self.logger.error(f"Check %(check)s FAILED (%(reason)s)", attr.asdict(result))

    async def ok(self, result):
        self.logger.info(f"Check %(check)s OK", attr.asdict(result))

    async def _recover(self, result):
        self.logger.warning(f"Check %(check)s RECOVERED", attr.asdict(result))

    async def _silenced_error(self, result):
        self.logger.info(f"Check %(check)s FAILED (%(reason)s)", attr.asdict(result))


class SMTPNotifier(BaseNotifier):
    pass
