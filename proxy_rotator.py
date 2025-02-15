import threading
import itertools


class ProxyRotator:
    def __init__(self, proxies):
        self._proxies_cycle = itertools.cycle(proxies)
        self._lock = threading.Lock()

    def get_next_proxy(self) -> str:
        with self._lock:
            return next(self._proxies_cycle)


with open("proxies.txt", "r") as proxies_file:
    proxies = [x.strip() for x in proxies_file.readlines()]

rotator = ProxyRotator(proxies)
