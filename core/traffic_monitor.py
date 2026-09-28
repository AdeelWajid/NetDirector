import time
import psutil


class TrafficMonitor:
    def __init__(self, counters=psutil.net_io_counters, clock=time.monotonic):
        self.counters = counters
        self.clock = clock
        self.previous = {}
        self.sampled_at = None

    def sample(self):
        current = self.counters(pernic=True)
        now = self.clock()
        elapsed = now - self.sampled_at if self.sampled_at is not None else 0
        result = {}
        for name, counter in current.items():
            before = self.previous.get(name)
            ready = before is not None and elapsed > 0
            result[name] = dict(received=counter.bytes_recv, sent=counter.bytes_sent,
                                down=max(0, counter.bytes_recv - before.bytes_recv) * 8 / elapsed / 1e6 if ready else None,
                                up=max(0, counter.bytes_sent - before.bytes_sent) * 8 / elapsed / 1e6 if ready else None)
        self.previous, self.sampled_at = current, now
        return result
