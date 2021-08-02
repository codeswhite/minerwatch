import json
from dataclasses import dataclass
from logging import getLogger

import requests

log = getLogger('prober')


@dataclass
class ProberConfig:
    addr: str


class EtherMineAPIProber:
    URL_BASE = 'https://api.ethermine.org/'

    def __init__(self, cfg: ProberConfig):
        log.info('Initializing Prober with config: %s',
                 json.dumps(cfg.__dict__))

        self.addr = cfg.addr

    def get_workers(self) -> (list, None):
        return self._get_endpoint('workers')

    def get_dashboard(self) -> (list, None):
        return self._get_endpoint('dashboard')

    def _get_endpoint(self, endpoint: str) -> (list, None):
        endpoint_url = EtherMineAPIProber.URL_BASE + \
            f'miner/{self.addr}/{endpoint}'
        try:
            resp = requests.get(endpoint_url)
        except requests.ConnectionError as err:
            log.error(
                'Connection error occurred when requesting workers endpoint:')
            log.error(err)
            return
        if resp.status_code != 200:
            log.error('Bad status code from server: [%d]', resp.status_code)
            return
        data = json.loads(resp.content)
        if data['status'] != 'OK':
            log.error('Got bad status in response body: [%s]', data["status"])
            return
        return data['data']
