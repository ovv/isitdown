import aiohttp
import logging

from yarl import URL

from .base import BaseChecks, Result

LOG = logging.getLogger(__name__)


class BaseHTTPCheck(BaseChecks):
    def __init__(self, url, *, method="GET", http_session=None, **kwargs):
        self.url = URL(url)

        if "name" not in kwargs:
            kwargs["name"] = f"{self.url.scheme}_check_{self.url.host}"

        super().__init__(**kwargs)
        self.method = method
        self.http_session = http_session

    async def startup(self):
        await super().startup()
        if not self.http_session:
            self.http_session = aiohttp.ClientSession()

    async def shutdown(self):
        await super().shutdown()
        await self.http_session.close()

    async def check(self):
        await super().check()
        response = await self.http_session.request(url=self.url, method=self.method)
        return await self.validate_response(response)

    async def validate_response(self, response):
        raise NotImplementedError()


class StatusCodeHTTPCheck(BaseHTTPCheck):
    def __init__(self, *, expected_status_code=200, **kwargs):
        super().__init__(**kwargs)
        self.expected_status_code = expected_status_code

    async def validate_response(self, response):
        if response.status == self.expected_status_code:
            result = Result(check=self.name, success=True, data=response)
        else:
            result = Result(
                check=self.name,
                success=False,
                data=response,
                reason=f"Wrong status code: {rep.status}",
            )

        return result
