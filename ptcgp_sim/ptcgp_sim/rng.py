
import random

class RNG:
    def __init__(self, seed: int):
        self.random = random.Random(seed)

    def choice(self, seq):
        # uniform choice
        return seq[self.random.randrange(len(seq))]

    def randint(self, a, b):
        return self.random.randint(a,b)
