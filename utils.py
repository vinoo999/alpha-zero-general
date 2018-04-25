class dotdict(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError

class ParallelRuntimes():
    def __init__(self, num_workers):
        self.max_len = num_workers
        self.runtimes = []

    def update(self, runtime):
        if len(self.runtimes) < self.max_len:
            self.runtimes.append(runtime)
        else:
            self.runtimes.pop(0)
            self.runtimes.append(runtime)

    def avg(self):
        return sum(self.runtimes) / len(self.runtimes)

    def eta(self, completed, total):
        return self.avg() * (total - completed) / self.max_len