import threading
import time


class FunctionSkipper:
    def __init__(self, skip_interval: float):
        self.last_called_times = {}  # id: last_called_time
        self.skip_interval = skip_interval
        self.lock = threading.Lock()

    def should_skip(self, id: any) -> bool:
        current_time = time.time()
        with self.lock:
            last_called_time = self.last_called_times.get(id, 0)
            if current_time - last_called_time < self.skip_interval:
                return True
            else:
                self.last_called_times[id] = current_time
                return False
