
class ChunkList(BenLazyList):
    # BenLazyList structure
    #
    # [.] denotes a lazylist
    #
    # [ [L] [[L] [L] [L] ...]]
    #  head  tail
    #
    # Lists in the tail are compressed
    #
    def __init__(self, data='ly2:lee', **kwargs):
        super(BenLazyListMutable, self).__init__(data=data, **kwargs)
        head, offset = decode_string(data, 1)
        self._head = head
        self._tail = ''.join('l', data[offset:])

    def encode(self):
        return ''.join(self._head[:-1], self.data[1:])

    def push(self, items):
        encoded = map(bencode, items)
        encoded.append(self._head[1:-1])
        size = 0
        last = len(encoded)
        for i in xrange(len(encoded) - 1, -1 ,-1):
            size += len(encoded[i])
            if size > COMPRESS_CHUNK_SIZE:
                chunk = ''.join('l', ''.join(encoded[i:last]), 'e')
                self._tail = ''.join('l',
                                     bencode(BenCompressed(BenLazyList(chunk))),
                                     self._tail[1:])
                last = i
                size = 0
        self._head = ''.join('l', ''.join(encoded[i:last]), 'e')

    def __iter__(self, recursive=True):
        def it(b):
            offset = 1
            while b[offset] != 'e':
                item, offset = self._decode(b, offset)
                if type(item) == BenLazyList and recursive:
                    for subitem in item:
                        yield subitem
                else:
                    yield item
        return chain(self.iter(self._head), self.iter(self._tail))

    def _default_decode(self, buf, offset):
        return decode_func[buf[offset]](buf, offset)

