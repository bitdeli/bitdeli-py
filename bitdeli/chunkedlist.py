from bencode import BenLazyList, BenCompressed, bencode, encoder_alias
from itertools import chain, imap, dropwhile

COMPRESS_CHUNK_SIZE = 65536

class ChunkedList(BenLazyList):
    # ChunkedList structure
    #
    # [L] denotes a lazylist
    # {L} denotes a compressed lazylist
    #
    # [ [L] | {L} {L} {L} ...]
    #  head  tail
    #
    # Both head and tail are optional initially.
    # Proper ChunkedLists always have a head.
    #
    def __init__(self, data='le', chunk_size=COMPRESS_CHUNK_SIZE, **kwargs):
        super(ChunkedList, self).__init__(data=data, **kwargs)
        self._chunk_size = min(chunk_size, COMPRESS_CHUNK_SIZE)
        if data[1] == 'y':
            head, offset = self._decode(data, 2)
            self._head = [head[1:-1]]
            self._head_size = len(head) - 2
            tail = data[offset:-1]
        else:
            self._head = []
            self._head_size = 0
            tail = data[1:-1]
        self._tail = []
        if tail:
            self._tail.append(tail)

    def encode(self):
        self._tail.append(bencode(self._encode_head()))
        self._tail.append('l')
        self._tail.reverse()
        self._tail.append('e')
        ret = ''.join(self._tail)
        self._head = None
        self._tail = None
        return ret

    def push(self, items):
        for item in reversed(map(bencode, items)):
            self._head.append(item)
            self._head_size += len(item)
            if self._head_size > self._chunk_size:
                chunk = bencode(BenCompressed(self._encode_head(),
                                              use_snappy=True))
                self._tail.append(chunk)
                self._head_size = 0
                self._head = []

    def _encode_head(self):
        self._head.append('l')
        self._head.reverse()
        self._head.append('e')
        return BenLazyList(''.join(self._head))

    def __iter__(self):
        return chain((self._decode(x, 0)[0] for x in reversed(self._head)),
                     chain.from_iterable(imap(self.iter, reversed(self._tail))))

    def __nonzero__(self):
        return 1 if self._tail or self._head else 0

    def drop_chunks(self, pred):
        def tail_predicate(chunk):
            # Check the first (newest) item of each chunk - drop the whole
            # chunk if the predicate fails. Note that since we check only
            # the first item, the chunk may still contain entries for which
            # the predicate would fail, so drop_chunks IS NOT guaranteed to
            # get rid of all the items in the tail which fail the predicate.
            #
            # The assumption is that the predicate will change over time and
            # eventually fail the first item, thus drop the chunk.
            return not (chunk and pred(self.iter(chunk).next()))
        def head_predicate(item):
            return not pred(self._decode(item, 0)[0])
        self._tail = list(dropwhile(tail_predicate, self._tail))
        if not self._tail:
            # head is cleaned only if there is nothing left in the tail.
            self._head = list(dropwhile(head_predicate, self._head))

encoder_alias(ChunkedList, BenLazyList)

if __name__ == '__main__':
    from bencode import bdecode, BenJson
    def test():
        c = ChunkedList(chunk_size=14)
        c.push(('0'))
        c.push(('1'))
        c.push(('2'))
        c.push(('a', 'b', 'c'))
        c.push(('d', 'e', 'f'))
        d = bdecode(bencode(c))
        d = ChunkedList(d.encode())
        d.push(('g', 'h', 'i'))
        print list(d)
        print list(bdecode(bencode(d)))

    def all():
        from cbencode import Decoder
        from itertools import islice
        import mmap, time
        dec = Decoder(json_decode=BenJson)
        f = file('/tmp/sa/testdata')
        buf = mmap.mmap(f.fileno(), 0, mmap.PROT_READ, mmap.MAP_SHARED)
        chu = ChunkedList()
        #it = islice(dec.decode_iter(buf), 500000)
        it = dec.decode_iter(buf)
        t1 = time.time()
        c = 0
        while True:
            try:
                n = it.next()
                chu.push((n,))
                c += 1
            except StopIteration:
                break
            chu.push(islice(it, 10))
            c += 10
        print 'iter (%d items) took %dms' % (c, (time.time() - t1) * 1000)
        buf = None
        f.close()
        t1 = time.time()
        enc = bencode(chu)
        print 'sze', len(bencode(chu))
        print 'encode took %dms' % ((time.time() - t1) * 1000)
        t1 = time.time()
        c = 0
        for item in dec.decode(enc): # bdecode(enc):
            c += 1
            #print item
        print 'decode (%d items) took %dms' % (c, (time.time() - t1) * 1000)

    def droptest():
        c = ChunkedList(chunk_size=7)
        for i in ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'):
            c.push((i,))
        c.drop_chunks(lambda x: x > 'f')
        for i in range(3):
            c.push((str(i),))
        print bool(c)
        print list(c)
        print list(bdecode(bencode(c)))

    droptest()
