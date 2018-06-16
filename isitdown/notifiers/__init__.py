import attr
import logging
import aiosmtplib

from enum import Enum
from email.mime.text import MIMEText

LOG = logging.getLogger(__name__)


class state(Enum):
    OK = 0
    ERROR = 1


@attr.s
class CheckState:

    name = attr.ib()
    state = attr.ib(default=state.OK, validator=attr.validators.in_(state))
    errors = attr.ib(default=0)
    notified = attr.ib(validator=bool, default=False)


class BaseNotifier:
    def __init__(self, notify_after=None):
        if notify_after is None:
            notify_after = (1,)

        self.check_states = dict()
        self.notify_after = notify_after

    async def error(self, result):
        if result.check not in self.check_states:
            self.check_states[result.check] = CheckState(name=result.check)

        check_state = self.check_states[result.check]
        check_state.state = state.ERROR

        try:
            await self._dispatch_error(check_state, result)
        except Exception:
            LOG.exception("Error while notifying: %s, state: ERROR", result.check)

    async def ok(self, result):
        if result.check not in self.check_states:
            self.check_states[result.check] = CheckState(name=result.check)

        check_state = self.check_states[result.check]

        if check_state.state == state.ERROR and check_state.notified:
            check_state.errors = 0
            check_state.state = state.OK
            check_state.notified = False

            try:
                await self._recover(result)
            except Exception:
                LOG.exception(
                    "Error while notifying: %s, state: %s",
                    result.check,
                    self.states[result.check],
                )
        else:
            check_state.errors = 0
            check_state.state = state.OK
            check_state.notified = False

            try:
                await self._ok(result)
            except Exception as e:
                LOG.exception(
                    "Error while notifying: %s, state: %s",
                    result.check,
                    self.states[result.check],
                )

    async def _dispatch_error(self, check_state, result):

        # Check if the error count is one where we should notify
        if check_state.errors in self.notify_after:
            check_state.notified = True
            await self._error(result)
            return

        # We notify if the error count is a multiple of the last notify_after value
        # This provide a backoff mechanisms
        if check_state.errors % self.notify_after[-1] == 0:
            check_state.notified = True
            await self._error(result)
        else:
            await self._silenced_error(result)

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

    async def _ok(self, result):
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

    async def _send_email(self, subject, payload=""):

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

    async def _ok(self, result):
        pass

    async def _silenced_error(self, result):
        pass
