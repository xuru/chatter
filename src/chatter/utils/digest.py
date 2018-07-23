import hashlib
import struct


def list_digest(strings):
    hash = hashlib.sha1()
    for s in strings:
        hash.update(struct.pack("I", len(s)))
        hash.update(s.encode('utf-8'))
    return hash.hexdigest()
