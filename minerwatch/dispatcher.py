import json
from logging import getLogger
from dataclasses import dataclass

import requests

log = getLogger('dispatcher')


@dataclass
class DispatcherConfig:
    use_telegram: bool
    tg_bot_token: str
    tg_chat_id: str


class Dispatcher:
    @classmethod
    def __init__(cls, cfg: DispatcherConfig):
        log.info('Initializing Dispatcher with config: %s', json.dumps(cfg.__dict__))
        if cfg.use_telegram:
            cls.telegram = TelegramNotifier({
                'token': cfg.tg_bot_token,
                'chat_id': cfg.tg_chat_id,
            })

    @classmethod
    def dispatch(cls, message: str):
        log.info('Dispatching a message: %s', message)
        if cls.telegram:
            cls.telegram.send_message(message)

    @classmethod
    def abs_high_stale_perc(cls, worker: str, percentage: float):
        percentage = round(percentage, 1)
        cls.dispatch(
            f'Worker "{worker}" stale shares percentage {percentage}% is high')

    @classmethod
    def delta_high_stale_perc(cls, worker: str, percentage: float, delta_time: int):
        percentage = round(percentage, 1)
        cls.dispatch(
            f'Worker "{worker}" stale shares percentage grew by +{percentage}% since last check ({delta_time} minutes ago)')

    @classmethod
    def disconnected(cls, worker: str):
        cls.dispatch(f'Worker "{worker}" disconnected!')

    @classmethod
    def hashrate_dropped(cls, worker: str, reported_hashrate_delta: float, prev_rep_mhs: float, rep_mhs: float, delta_time: int):
        reported_hashrate_delta = round(reported_hashrate_delta, 1)
        prev_rep_mhs = round(prev_rep_mhs, 1)
        rep_mhs = round(rep_mhs, 1)
        cls.dispatch(
            f'Worker "{worker}" have dropped its hashrate by {reported_hashrate_delta}% (from {prev_rep_mhs}MH/s to {rep_mhs}MH/s) from last check ({delta_time} minutes ago)')


class TelegramNotifier:
    def __init__(self, config: dict):
        self.token = config['token']
        self.chat_id = config['chat_id']

    def send_message(self, message: str) -> bool:
        send_text = f'https://api.telegram.org/bot{self.token}/sendMessage'
        response = requests.get(send_text, {
            'chat_id': self.chat_id,
            'parse_mode': 'HTML',
            'text': message,
        })
        return response.json()['ok']  # Return success?
