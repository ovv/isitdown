import attr
import logging
import aiosmtplib

from enum import Enum
from email.mime.text import MIMEText

LOG = logging.getLogger(__name__)


class state(Enum):
    OK = 0
    ERROR = 1


class BaseNotifier:
    def __init__(self, notify_after=1):
        self.errors = 0
        self.state = state.OK
        self.notify_after = notify_after

    async def error(self, result):
        self.state = state.ERROR
        self.errors += 1
        if self.errors % self.notify_after == 0:
            await self._error(result)
        else:
            await self._silenced_error(result)

    async def ok(self, result):
        if self.state == state.ERROR:
            self.state = state.OK
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
    def __init__(
        self,
        *,
        hostname,
        sender,
        recipients,
        username=None,
        password=None,
        port=None,
        use_tls=None,
        smtp_kwargs=None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        if not smtp_kwargs:
            smtp_kwargs = dict()

        smtp_kwargs["hostname"] = hostname
        if port is not None:
            smtp_kwargs["port"] = port
        if use_tls is not None:
            smtp_kwargs["use_tls"] = use_tls

        if not isinstance(recipients, (list, tuple)):
            recipients = (recipients,)

        self.sender = sender
        self.username = username
        self.password = password
        self.recipients = recipients
        self.smtp_kwargs = smtp_kwargs

    async def _send_email(self, subject, payload):

        client = aiosmtplib.SMTP(**self.smtp_kwargs)
        await client.connect()

        if self.username and self.password:
            await client.login(username=self.username, password=self.password)

        message = MIMEText(payload)
        message["To"] = ", ".join(self.recipients)
        message["From"] = self.sender
        message["Subject"] = subject
        await client.send_message(message)

    async def _error(self, result):
        await self._send_email(
            subject=f"Check {result.check} FAILED ({result.reason}) !",
            payload=str(result.data),
        )

    async def _recover(self, result):
        await self._send_email(subject=f"Check {result.check} RECOVERED !")

    async def ok(self, result):
        pass

    async def _silenced_error(self, result):
        pass
