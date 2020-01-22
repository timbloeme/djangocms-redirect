# -*- coding: utf-8 -*-
import hashlib


def get_key_from_path_and_site(path, site_id):
    """
    cache key has to be < 250 chars to avoid memcache.Client.MemcachedKeyLengthError.

    SHA-224 is the best algorithm whose output (224 chars) respects this limitations:

    total key length: Prefix (11) + HASH (224) + ID (max 3) + 2 separators (2) = 240
    """
    hashed_path = hashlib.sha224(path.encode('utf-8')).hexdigest()
    key = 'CMSREDIRECT:{}:{}'.format(hashed_path, site_id)
    return key
