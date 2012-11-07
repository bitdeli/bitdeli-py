
class CountIter(object):
    def __init__(self, it):
        self.count = 0
        self.it = it

    def __iter__(self):
        for x in self.it:
            self.count += 1
            yield x

