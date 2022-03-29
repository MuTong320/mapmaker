from numpy import random


class RandomBase:
    def __init__(self, seed=None):
        self.set_random_seed(seed)

    def set_random_seed(self, seed=None):
        if not seed:
            self.seed = random.randint(10000)
        else:
            self.seed = int(seed)
        random.seed(self.seed)