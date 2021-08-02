import time
import json
from logging import getLogger
from dataclasses import dataclass

from minerwatch import Dispatcher, EtherMineAPIProber

log = getLogger('manager')


@dataclass
class ManagerConfig:
    timer_interval: int
    abs_stale_treshold: float
    delta_stale_treshold: float
    hashrate_drop_treshold: float


class Manager:
    is_first_tick = True
    workers: dict

    def __init__(self, cfg: ManagerConfig, prober: EtherMineAPIProber, dispatcher: Dispatcher):
        self.prober = prober
        self.dispatcher = dispatcher

        # Init manager
        log.info('Initializing Manager with config: %s', json.dumps(cfg.__dict__))

        self.timer_interval = cfg.timer_interval
        self.abs_stale_treshold = cfg.abs_stale_treshold
        self.delta_stale_treshold = cfg.delta_stale_treshold
        self.hashrate_drop_treshold = cfg.hashrate_drop_treshold

        # Run first probe and timer loop
        self.workers = self._get_workers()
        try:
            while 1:
                time.sleep(self.timer_interval * 60)
                self.tick(self._probe_workers())
        except KeyboardInterrupt:
            log.info('Got SIGHUP, closing')

    def tick(self, workers_data: dict):
        '''
        * Report upon:
            # Num of workers is not what we expect
            # One of the workers have high stale share percentage
            # One of the workers have dropped its reported hashrate
        '''
        # Check num of workers is what is expected
        active = len(workers_data)
        log.debug('Currently there are %d active workers', active)
        stored_active = len(self.workers)
        if active != stored_active:
            if active > stored_active:
                log.info('Identified worker differential: Connected :)')
            else:
                for name in [w['worker'] for w in self.workers]:
                    if name not in [w['worker'] for w in workers_data]:
                        self.dispatcher.disconnected(name)

        for i, w in enumerate(workers_data):
            name = w['worker']

            # Check percentage of stales
            prev_stale_perc = _calc_stale_percentage(self.workers[i])
            stales_perc = _calc_stale_percentage(w)

            stale_abs_prevail = (
                stales_perc > self.abs_stale_treshold
            ) and (
                self.is_first_tick or prev_stale_perc < self.abs_stale_treshold
            )
            if stale_abs_prevail:
                self.dispatcher.abs_high_stale_perc(
                    w['worker'], stales_perc)

            stale_delta = stales_perc - prev_stale_perc
            stale_delta_prevail = stale_delta > self.delta_stale_treshold
            if stale_delta_prevail:
                self.dispatcher.delta_high_stale_perc(
                    w['worker'], stales_perc, self.timer_interval)

            # Check hashrate drop
            reported_hashrate_delta = 100 * \
                (1 - self.workers[i]['reportedHashrate'] /
                 w['reportedHashrate'])
            if reported_hashrate_delta < -self.hashrate_drop_treshold:
                self.dispatcher.hashrate_dropped(
                    name, reported_hashrate_delta,
                    self.workers[i]['reportedHashrate'] / 1000000,
                    w['reportedHashrate'] / 1000000,
                    self.timer_interval
                )

            # Debug info about parsed worker
            stat = f'Finished parsing worker "{name}": '
            if round(stales_perc, 1) != 0.0:
                stat += '[stales_perc=%.1f%%],' % stales_perc
            if round(stale_delta, 1) != 0.0:
                stat += '[stales_perc_delta=%.1f%%],' % stale_delta
            if round(reported_hashrate_delta, 1) != 0.0:
                stat += '[reported_hashrate_delta=%.1f%%],' % reported_hashrate_delta
            log.debug(stat)

        # Store worker data
        self.workers = workers_data
        self.is_first_tick = False

    def _get_workers(self) -> (None, dict):
        return self.prober.get_workers()


def _calc_stale_percentage(worker: dict) -> float:
    return 100 * worker['staleShares'] / worker['validShares']
