import os
import sys
import json
from bencode import bencode
from cbencode import Decoder
from itertools import islice

OUTPUT_CHUNK_SIZE = 16 * 1024 * 1024

nonce = ''

def all_inputs():
    communicate('resetinputs')
    while True:
        path = communicate('nextinput')
        if len(path) > 0:
            yield path
        else:
            break

def entries(decoder=Decoder()):
    while True:
        for entry in communicate('next', decoder=decoder):
            if len(entry) > 0:
                yield entry[0], entry[1]
            else:
                return

def output(lst, chunked=False):
    def next_chunk(it):
        size = 0
        while size < OUTPUT_CHUNK_SIZE:
            enc = bencode(it.next())
            size += len(enc)
            yield enc
    if chunked:
        it = iter(lst)
        while True:
            chunk = list(next_chunk(it))
            if chunk:
                communicate('out', bencode(chunk))
            else:
                break
    else:
        communicate('out', bencode(map(bencode, lst)))

def output_sys(key, value):
    return communicate('sysmsg', bencode([key, value]))

def done():
    return communicate('done')

def ping():
    return communicate('ping')

def log(msg):
    communicate('log', bencode(unicode(msg).encode('utf-8')))

def params():
    return communicate('params')

#
# low-level protocol handling
#

class LogWriter(object):
    def write(self, string):
        string = string.strip()
        if string:
            log(string)

def communicate(head, body='', decoder=Decoder()):
    sys.__stdout__.write('%s %s %d %s\n' % (nonce, head, len(body), body))
    reply = recv()
    if reply:
        if reply[0] == 'l':
            return decoder.decode_iter(reply)
        else:
            return decoder.decode(reply)

def read_int():
    buf = ''
    for i in range(11):
        buf += sys.stdin.read(1)
        if buf[-1] == ' ':
            return int(buf)
    raise Exception("System error: Invalid length (%s)" % buf)

def recv():
    global nonce
    nonce = sys.stdin.read(5)[:4]
    return sys.stdin.read(read_int())

def init():
    global recv
    if 'TESTING' not in os.environ:
        sys.stdout = LogWriter()
        ret = recv()
        if ret != '2:ok':
            raise Exception("System error: Invalid initial reply (%s)" % ret)
        ping()
    else:
        recv = lambda: ''

init()

