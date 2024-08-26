import time


class Rate:
    def __init__(self, hz=1):
        self.next_time = None
        self.last_time = None
        self.rate_hz = hz
        self.rate_s = 0.01 # 1.0 / self.rate_hz
        self.counter = 0


    def limit_rate(self, cond=True):
        self.counter += 1
        print(f"{self.next_time}, {self.rate_s}, {self.counter}")
        input()
        if self.next_time is not None:
            curr_time = time.time()
            print(curr_time)
            time_diff = self.next_time - curr_time
            if time_diff > 0 and cond:
                time.sleep(time_diff)
                self.next_time = self.next_time + 0.1
                self.last_time = time.time()
                return cond
            else:
                self.last_time = time.time()
                return cond
        else:
            self.next_time = time.time() + self.rate_s
            self.last_time = time.time()
            return cond