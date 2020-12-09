"""
    Author: LI Rui lir@bupt.edu.cn
    All rights reserved.
"""
import base64
from base64 import b64encode,b64decode
from Crypto.Cipher import AES
from utils.config import SEC_KEY

def encryAES(str):
    key = SEC_KEY.encode()
    header = b"courierC00lA3S"
    data = str.encode()
    nonce = base64.b64decode(b"b8px/5uta6loJ0OkSG4S")
    cipher = AES.new(key, AES.MODE_OCB, nonce=nonce)
    cipher.update(header)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
    json_v = [ b64encode(x).decode('utf-8') for x in [cipher.nonce, header, ciphertext, tag] ]
    result = dict(zip(json_k, json_v))
    return result

def decryAES(ciphertext, tag):
    try:
        key = SEC_KEY.encode()
        nonce = base64.b64decode(b"b8px/5uta6loJ0OkSG4S")
        header = b"courierC00lA3S"
        ciphertext = b64decode(ciphertext)
        tag = b64decode(tag)
        cipher = AES.new(key, AES.MODE_OCB, nonce)
        cipher.update(header)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext.decode()
    except:
        raise Exception("CRYERR")