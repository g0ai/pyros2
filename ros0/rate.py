import time


class Rate:
    def __init__(self, hz=1):
        self.next_time = None
        self.rate_hz = hz
        self.rate_s = 1.0 / self.rate_hz


    def limit_rate(self, cond=True):
        if self.next_time is not None:
            curr_time = time.perf_counter()
            time_diff = self.next_time - curr_time
            if time_diff > 0 and cond:
                time.sleep(time_diff)
                self.next_time += self.rate_s
                return cond
            else:
                return cond
        else:
            self.next_time = time.perf_counter() + self.rate_s
            return cond