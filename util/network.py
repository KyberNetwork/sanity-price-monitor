from enum import Enum, auto
from json import dumps
from urllib.parse import urlencode, unquote, urlparse, parse_qsl, ParseResult

import aiohttp
import async_timeout


class DataFormat(Enum):
    TEXT = auto()
    JSON = auto()


async def get_response_content_from_get_request(url, headers=None, params=None, timeout=30, format=DataFormat.TEXT):
    async with aiohttp.ClientSession(headers=headers) as session:
        with async_timeout.timeout(timeout):
            async with session.get(url=url, params=params) as response:
                return await response.json() if format == DataFormat.JSON else await response.text()


async def get_response_content_from_post_request(url, headers=None, payload=None, timeout=30, format=DataFormat.TEXT):
    if payload is None:
        payload = {}
    async with aiohttp.ClientSession(headers=headers) as session:
        with async_timeout.timeout(timeout):
            async with session.post(url=url, data=payload) as response:
                return await response.json() if format == DataFormat.JSON else await response.text()


def add_url_params(url, params):
    """ Add GET params to provided URL being aware of existing.

    :param url: string of target URL
    :param params: dict containing requested params to be added
    :return: string with updated URL

    >> url = 'http://stackoverflow.com/test?answers=true'
    >> new_params = {'answers': False, 'data': ['some','values']}
    >> add_url_params(url, new_params)
    'http://stackoverflow.com/test?data=some&data=values&answers=false'
    """
    # Unquoting URL first so we don't loose existing args
    url = unquote(url)
    # Extracting url info
    parsed_url = urlparse(url)
    # Extracting URL arguments from parsed URL
    get_args = parsed_url.query
    # Converting URL arguments to dict
    parsed_get_args = dict(parse_qsl(get_args))
    # Merging URL arguments dict with new params
    parsed_get_args.update(params)

    # Bool and Dict values should be converted to json-friendly values
    # you may throw this part away if you don't like it :)
    parsed_get_args.update(
        {k: dumps(v) for k, v in parsed_get_args.items()
         if isinstance(v, (bool, dict))}
    )

    # Converting URL argument to proper query string
    encoded_get_args = urlencode(parsed_get_args, doseq=True)
    # Creating new parsed result object based on provided with new
    # URL arguments. Same thing happens inside of urlparse.
    new_url = ParseResult(
        parsed_url.scheme, parsed_url.netloc, parsed_url.path,
        parsed_url.params, encoded_get_args, parsed_url.fragment
    ).geturl()

    return new_url
