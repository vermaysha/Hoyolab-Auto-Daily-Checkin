import json
import requests
from log import logging
from requests.exceptions import HTTPError

class HttpRequest(object):
    @staticmethod
    def to_python(json_str: str):
        return json.loads(json_str)

    @staticmethod
    def to_json(obj):
        return json.dumps(obj, indent=4, ensure_ascii=False)

    def request(self, method, url, max_retry: int = 3,
            params=None, data=None, json=None, headers=None, **kwargs):
        for i in range(max_retry + 1):
            try:
                s = requests.Session()
                response = s.request(method, url, params=params,
                    data=data, json=json, headers=headers, **kwargs)
            except HTTPError as e:
                logging.error(f'HTTP error:\n{e}')
                logging.error(f'The NO.{i + 1} request failed, retrying...')
            except KeyError as e:
                logging.error(f'Wrong response:\n{e}')
                logging.error(f'The NO.{i + 1} request failed, retrying...')
            except Exception as e:
                logging.error(f'Unknown error:\n{e}')
                logging.error(f'The NO.{i + 1} request failed, retrying...')
            else:
                return response

        raise Exception(f'All {max_retry + 1} HTTP requests failed, die.')


req = HttpRequest()