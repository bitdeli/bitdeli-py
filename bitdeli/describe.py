from profiles import Op, register_op
from collections import Counter, Mapping
from itertools import islice

def default_features(mapping, prefix='', exclude=[], include=[]):
    for key, value in mapping.iteritems():
        if key.startswith('_') or\
           key.startswith('!') or\
           key in exclude or\
           (include and key not in include):
            continue
        item = '%s%s' % (prefix, key)
        if isinstance(value, Mapping):
            for x in default_features(value,
                                      prefix='%s:' % item,
                                      exclude=exclude,
                                      include=include):
                yield x
        elif isinstance(value, basestring):
            yield '%s:%s' % (item, value)
        else:
            yield item

class Describe(Op):
    def __init__(self,
                 parent,
                 classify,
                 features=default_features,
                 min_frequency=10,
                 num_top_features=10,
                 num_top_segments=10,
                 exclude_specific=True):
        self.classify = classify
        self.features = features
        self.min_frequency = min_frequency
        self.num_top_features = num_top_features
        self.num_top_segments = num_top_segments
        self.exclude_specific = exclude_specific
        self.segments = {}
        self.freqs = Counter()
        self.segment_sizes = Counter()
        super(Describe, self).__init__(parent)

    def _iter(self, it):
        freqs = self.freqs
        for profile in it:
            features = list(self.features(profile))
            freqs.update(features)
            for segment in self.classify(profile):
                self.segment_sizes[segment] += 1
                stats = self.segments.get(segment, None)
                if not stats:
                    self.segments[segment] = stats = Counter()
                stats.update(features)
        self.freqs = dict(x for x in self.freqs.iteritems()\
                          if x[1] > self.min_frequency)
        return self

    def stats(self):
        return self.segments, self.freqs, self.segment_sizes

    def distinctive_segments(self):
        def stats_score(stats, freqs):
            for key, freq in stats.iteritems():
                f = freqs.get(key, None)
                if f and not (self.exclude_specific and f == freq):
                    yield (freq / float(f)), key

        def segment_score():
            for segment, stats in self.segments.iteritems():
                top = list(sorted(stats_score(stats, self.freqs),
                           reverse=True))[:self.num_top_features]
                yield sum(score for score, key in top), segment, top

        return sorted(segment_score(), reverse=True)

    def __iter__(self):
        for score, segment, top in islice(self.distinctive_segments(),
                                          self.num_top_segments):
            label = '%s (%d profiles)' % (segment, self.segment_sizes[segment])
            stats = self.segments[segment]
            yield {'type': 'table',
                   'size': (12, 5),
                   'label': label,
                   'chart': {'score': 'bar'},
                   'data': [{'feature': f, 'score': s, '#profiles': stats[f]}
                            for s, f in top]}

register_op('describe', Describe)
