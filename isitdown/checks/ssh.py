import re
import logging
import asyncssh

from .base import BaseChecks, Result

LOG = logging.getLogger(__name__)


class BaseSSHCommandCheck(BaseChecks):
    def __init__(
        self,
        *,
        command,
        host,
        port=None,
        username=None,
        password=None,
        ssh_kwargs=None,
        **kwargs,
    ):
        if not ssh_kwargs:
            ssh_kwargs = dict()

        ssh_kwargs["host"] = host
        if port is not None:
            ssh_kwargs["port"] = port
        if username is not None:
            ssh_kwargs["username"] = username
        if password is not None:
            ssh_kwargs["password"] = password

        if "name" not in kwargs:
            kwargs["name"] = f"command_check_{host}_{command}"

        super().__init__(**kwargs)
        self.host = host
        self.command = command
        self.ssh_kwargs = ssh_kwargs

    async def check(self):
        await super().check()

        async with asyncssh.connect(**self.ssh_kwargs) as connection:
            response = await connection.run(self.command)

        return await self.validate_response(response)

    async def validate_response(self, response):
        raise NotImplementedError()


class ExitCodeSSHCommandCheck(BaseSSHCommandCheck):
    def __init__(self, *, expected_exit_code=0, **kwargs):
        super().__init__(**kwargs)
        self.expected_exit_code = expected_exit_code

    async def validate_response(self, response):
        if response.exit_status == 0:
            result = Result(check=self.name, success=True, data=response)
        else:
            result = Result(
                check=self.name,
                success=False,
                data=response,
                reason=f"Exit code is: {response.exit_status}",
            )

        return result


class StdoutSSHCommandCheck(BaseSSHCommandCheck):
    def __init__(self, *, expected_regex, **kwargs):
        super().__init__(**kwargs)
        self.expected_regex = expected_regex
        self.expected_regex_compiled = re.compile(self.expected_regex)

    async def validate_response(self, response):
        if re.search(self.expected_regex_compiled, response.stdout):
            result = Result(check=self.name, success=True, data=response)
        else:
            result = Result(
                check=self.name,
                success=False,
                data=response,
                reason=f"No match for: {self.expected_regex}",
            )

        return result
