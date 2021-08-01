#!/usr/bin/python3

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

from minerwatch import (
    DictConfig, Manager, ManagerConfig,
    Dispatcher, DispatcherConfig,
    EtherMineAPIProber, ProberConfig
)


class Defaults:
    config_path = Path.home().joinpath('.config', 'minerwatch.json')
    # data is cached on server for 2min and the max cap is 100req/15min
    timer_interval = 4.0
    abs_stale_treshold = 4.0
    delta_stale_treshold = 1.5
    hashrate_drop_treshold = 3.0

    @staticmethod
    def get_config_defaults():
        d = {
            'address': '',
            'timer_interval': Defaults.timer_interval,
            'no_notify_abs_stale': False,
            'abs_stale_treshold': Defaults.abs_stale_treshold,
            'no_notify_delta_stale': False,
            'delta_stale_treshold': Defaults.delta_stale_treshold,
            'no_notify_hashrate_drop': False,
            'hashrate_drop_treshold': Defaults.hashrate_drop_treshold,
            'use_telegram': True,
            'tg_bot_token': '',
            'tg_chat_id': '',
        }
        return d


def parse_args():
    from argparse import ArgumentParser
    parser = ArgumentParser('MinerWatch')

    # General
    parser.add_argument('--debug', action='store_true',
                        help='Show verbose debug info')
    parser.add_argument('--log-file', type=str,
                        help='File to log into (default: STDOUT)')
    parser.add_argument('-a', '--addr', type=str,
                        help='Address to watch')
    parser.add_argument('--config', type=str, default=Defaults.config_path,
                        help=f'Path to config file (default: {str(Defaults.config_path)})')
    parser.add_argument('--timer-interval', type=float, default=Defaults.timer_interval,
                        help=f'Checks interval in minutes (min: 2.5), (default: {Defaults.timer_interval})')

    # Checks and notifications
    parser.add_argument('--no-notify-abs-stale', action='store_true',
                        help="Don't notify about absolute high stale shares percentage")
    parser.add_argument('--abs-stale-treshold', type=float, default=Defaults.abs_stale_treshold,
                        help=f'Absolute stale shares percentage to notify (default: {Defaults.abs_stale_treshold})')
    parser.add_argument('--no-notify-delta-stale', action='store_true',
                        help="Don't notify about stale shares high delta percentage")
    parser.add_argument('--delta-stale-treshold', type=float, default=Defaults.delta_stale_treshold,
                        help=f'Delta stale shares percentage to notify (default: {Defaults.delta_stale_treshold})')
    parser.add_argument('--no-notify-hashrate-drop', action='store_true',
                        help="Don't notify about hashrate drop")
    parser.add_argument('--hashrate-drop-treshold', type=float, default=Defaults.hashrate_drop_treshold,
                        help=f'Delta hashrate drop percentage to notify (default: {Defaults.hashrate_drop_treshold})')

    # Dispatcher
    parser.add_argument('--no-telegram', action='store_true',
                        help="Don't dispatch notifications to telegram")
    parser.add_argument('--tg-bot-token', type=str, help='Telegram bot token')
    parser.add_argument('--tg-chat-id', type=str, help='Telegram chat ID')

    return parser.parse_args()


def main():
    # Parse args
    args = parse_args()
    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG

    handlers = [
        logging.StreamHandler(sys.stdout)
    ]
    if args.log_file:
        log_file = Path(args.log_file).resolve()
        log_file.parent.mkdir(exist_ok=True)

        handlers = [
            RotatingFileHandler(
                filename=log_file, mode='w',
                maxBytes=256 * 1024, backupCount=5, encoding='utf-8')
        ]

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p', level=log_level,
                        handlers=handlers)

    # Parse config
    conf = DictConfig(args.config, Defaults.get_config_defaults())

    # Prober configurations
    addr = conf['address']
    if args.addr:
        addr = args.addr

    if not addr:
        logging.error(
            'No address specified, please edit config file or pass address by argument')
        return -1  # exit

    # Dispatcher configurations
    use_telegram = conf['use_telegram']
    if args.no_telegram:
        use_telegram = False
    tg_bot_token = conf['tg_bot_token']
    if args.tg_bot_token:
        tg_bot_token = args.tg_bot_token
    tg_chat_id = conf['tg_chat_id']
    if args.tg_chat_id:
        tg_chat_id = args.tg_chat_id

    if use_telegram:
        if not tg_bot_token:
            logging.error(
                'No Telegram bot token specified, please edit config file or pass by argument')
            return -1
        if not tg_chat_id:
            logging.error(
                'No Telegram chat ID specified, please edit config file or pass by argument')
            return -1

    # Manager configurations
    timer_interval = conf['timer_interval']
    if args.timer_interval:
        timer_interval = args.timer_interval
    abs_stale_treshold = conf['abs_stale_treshold']
    if args.abs_stale_treshold:
        abs_stale_treshold = args.abs_stale_treshold
    delta_stale_treshold = conf['delta_stale_treshold']
    if args.delta_stale_treshold:
        delta_stale_treshold = args.delta_stale_treshold
    hashrate_drop_treshold = conf['hashrate_drop_treshold']
    if args.hashrate_drop_treshold:
        hashrate_drop_treshold = args.hashrate_drop_treshold

    # Init Prober & Dispatcher and run Manager
    Manager(ManagerConfig(
        timer_interval,
        abs_stale_treshold,
        delta_stale_treshold,
        hashrate_drop_treshold
    ),
        EtherMineAPIProber(ProberConfig(
            addr
        )),
        Dispatcher(DispatcherConfig(
            use_telegram,
            tg_bot_token,
            tg_chat_id,
        ))
    )


if __name__ == '__main__':
    exit(main())
