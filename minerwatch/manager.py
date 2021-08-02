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
    _cached: list

    def __init__(self, cfg: ManagerConfig, prober: EtherMineAPIProber, dispatcher: Dispatcher):
        self.prober = prober
        self.dispatcher = dispatcher

        # Init manager
        log.info('Initializing Manager with config: %s',
                 json.dumps(cfg.__dict__))

        self.timer_interval = cfg.timer_interval
        self.abs_stale_treshold = cfg.abs_stale_treshold
        self.delta_stale_treshold = cfg.delta_stale_treshold
        self.hashrate_drop_treshold = cfg.hashrate_drop_treshold

        # Run first probe and timer loop
        self._cached = self._probe_workers()
        try:
            while 1:
                time.sleep(self.timer_interval * 60)
                self.tick()
        except KeyboardInterrupt:
            log.info('Got SIGHUP, closing')

    def tick(self):
        '''
        * Report upon:
            # Num of workers is not what we expect
            # One of the workers have high stale share percentage
            # One of the workers have dropped its reported hashrate
        '''
        workers_data = self._probe_workers()

        # Check num of workers is what is expected
        active = len(workers_data)
        log.debug('Currently there are %d active workers', active)
        stored_active = len(self._cached)
        if active != stored_active:
            if active > stored_active:
                log.info('Identified worker differential: Connected :)')
            else:
                for name in [w['worker'] for w in self._cached]:
                    if name not in [w['worker'] for w in workers_data]:
                        self.dispatcher.disconnected(name)

        for wrk in workers_data:
            name = wrk['worker']
            status_text = f'Finished parsing worker "{name}": '

            # Load previous fetch (cache)
            cached = None
            for worker in self._cached:
                if worker['worker'] == name:
                    cached = worker

            # Check percentage of stales
            stales_perc = _calc_stale_percentage(wrk)

            if cached:
                cached_stale_perc = _calc_stale_percentage(cached)
                is_cached_stale_abs_prevail = cached_stale_perc > self.abs_stale_treshold

                # Check stale percentage differential from cached
                stale_delta = stales_perc - cached_stale_perc
                stale_delta_prevail = stale_delta > self.delta_stale_treshold
                if stale_delta_prevail:
                    self.dispatcher.delta_high_stale_perc(
                        wrk['worker'], stales_perc, self.timer_interval)

            # Check absolute stale percentage level (avoid dispatching twice in a row)
            is_stale_abs_prevail = stales_perc > self.abs_stale_treshold
            if is_stale_abs_prevail and (
                not cached or not is_cached_stale_abs_prevail
            ):
                self.dispatcher.abs_high_stale_perc(
                    wrk['worker'], stales_perc)

            # Check hashrate drop
            current_reported = wrk['reportedHashrate'] / 1000000
            if cached and current_reported != 0:
                cached_reported = cached['reportedHashrate'] / 1000000
                reported_hashrate_delta = 100 * \
                    (1 - cached_reported / current_reported)
                if reported_hashrate_delta < -self.hashrate_drop_treshold:
                    self.dispatcher.hashrate_dropped(
                        name, reported_hashrate_delta,
                        cached_reported, current_reported, self.timer_interval
                    )

            # Debug info about parsed worker
            if round(stales_perc, 1) != 0.0:
                status_text += '[stales_perc=%.1f%%],' % stales_perc
            if round(stale_delta, 1) != 0.0:
                status_text += '[stales_perc_delta=%.1f%%],' % stale_delta
            if round(reported_hashrate_delta, 1) != 0.0:
                status_text += '[reported_hashrate_delta=%.1f%%],' % reported_hashrate_delta
            log.debug(status_text)

        # Store worker data for next tick's cache
        self._cached = workers_data

    def _probe_workers(self) -> (None, list):
        return self.prober.get_workers()


def _calc_stale_percentage(worker: dict) -> float:
    valid, stale = worker['validShares'], worker['staleShares']
    if valid == 0:
        return 0
    return 100 * stale / valid
