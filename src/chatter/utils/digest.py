import hashlib
import struct
from typing import List, Dict


def get_digest(obj):
    if isinstance(obj, str):
        return str_digest(obj)
    elif isinstance(obj, dict):
        return hash_digest(obj)
    elif isinstance(obj, (list, set)):
        return list_digest(list(obj))


def list_digest(strings: List[str]):
    hash = hashlib.sha1()
    for s in strings:
        hash.update(struct.pack("I", len(s)))
        hash.update(s.encode('utf-8'))
    return hash.hexdigest()


def hash_digest(data: Dict[str, str]):
    hash = hashlib.sha1()
    for k, v in data.items():
        s = f"{k}:{str_digest(v)}"
        hash.update(struct.pack("I", len(s)))
        hash.update(s.encode('utf-8'))
    return hash.hexdigest()


def str_digest(text: str):
    hash = hashlib.sha1()
    hash.update(text.encode('utf-8'))
    return hash.hexdigest()
