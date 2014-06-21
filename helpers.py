# -*- coding: utf-8 -*-
import hashlib
import re

def sha1_string(s):
    sha1_checksum = hashlib.sha1()
    sha1_checksum.update(s)
    return sha1_checksum.hexdigest()

def force_unicode(text):
    if text == None:
        return u''

    if isinstance(text, unicode):
        return text

    try:
        text = unicode(text, 'utf-8')
    except UnicodeDecodeError:
        text = unicode(text, 'latin1')
    except TypeError:
        text = unicode(text)
    return text

def force_utf8(text):
    return str(force_unicode(text).encode('utf8'))
