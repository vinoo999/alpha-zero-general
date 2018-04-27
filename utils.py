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


def check_platform():
    from sys import platform

    if platform == "linux" or platform == "linux2":
        return True
    elif platform == "darwin":
        print(" *** WARNING *** MacOS does not support the necessary synchronization primitives for Python 3 multiprocessing queues. Defaulting to 1 worker. *** WARNING *** ")
    elif platform == "win32":
        print(" *** WARNING *** Not tested on Windows. Stability not guaranteed with multiple workers. *** WARNING *** ")
    else:
        print(" *** WARNING *** Unknown platform. Stability not guaranteed with multiple workers. *** WARNING *** ")

    return False
