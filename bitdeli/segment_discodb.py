from itertools import ifilter
from discodb import DiscoDBInquiry, DiscoDBItemInquiry
from discodb.query import Literal

class SegmentDiscoDBInquiry(DiscoDBInquiry):
    def __init__(self, iterfunc, okfunc):
        self.iterfunc = iterfunc
        self.okfunc = okfunc

    def __iter__(self):
        return ifilter(self.okfunc, self.iterfunc())

    def __len__(self):
        return sum(1 for _ in self)

class SegmentDiscoDB(object):

    def __init__(self, db, segments, uidfunc, labels):
        self.labels = labels
        self.db = db
        n = len(segments)
        if uidfunc:
            if n == 1:
                seg = segments[0]
                self.ok = lambda value: uidfunc(value) in seg
            elif n == 2:
                seg0, seg1 = segments
                def two(value):
                    uid = uidfunc(value)
                    return uid in seg0 and uid in seg1
                self.ok = two
            else:
                def many(value):
                    uid = uidfunc(value)
                    for segment in segments:
                        if uid not in segment:
                            return False
                    return True
                self.ok = many
        else:
            def isect():
                segs = sorted((len(s), s) for s in segments)
                tail = segs[1:]
                for uid in segs[0][1]:
                    for sze, seg in tail:
                        if uid not in seg:
                            break
                    else:
                        yield uid
            self.ok = None
            self.view = db.make_view(segments[0] if n == 1 else isect())

    def __contains__(self, key):
        return key in self.db

    def __iter__(self):
        return iter(self.db)

    def __len__(self):
        return len(self.db)

    def __str__(self):
        return '%s({%s})' % (self.__class__.__name__,
                             self.items().__format__('%s: %s.3'))

    def __getitem__(self, key):
        if self.ok:
            return SegmentDiscoDBInquiry(lambda: self.db[key], self.ok)
        else:
            return self.db.query(Literal(key), view=self.view)

    def get(self, key, default=None):
        if key in self:
            return self[key]
        return default

    def items(self):
        return DiscoDBItemInquiry(lambda: ((k, self[k]) for k in self))

    def keys(self):
        return self.db.keys()

    def values(self):
        return SegmentDiscoDBInquiry(lambda: self.db.values(), self.ok)

    def unique_values(self):
        return SegmentDiscoDBInquiry(lambda: self.db.unique_values(), self.ok)

    def query(self, query):
        if self.ok:
            return SegmentDiscoDBInquiry(lambda: self.db.query(query), self.ok)
        else:
            return self.db.query(query, view=self.view)

    def peek(self, key, default=None):
        try:
            return iter(self.get(key, [])).next()
        except StopIteration:
            return default
