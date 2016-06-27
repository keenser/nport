#!/usr/bin/env python3.4

import re
import sys
import binascii

def pem(pemfile):
    import base64
    pkey = []
    def derparser(data, length):
        l = 0
        while l < length:
            btype = data[l]
            l+=1
            if data[l] > 0x80:
                plen = data[l]-0x80
                blen = int.from_bytes(data[l+1:l+1+plen],'big')
                l+=plen
            else:
                blen = data[l]
            l+=1

            if btype == 0x30:
                l += derparser(data[l:l+blen], blen)
            elif btype == 0x02:
                pkey.append({'size': blen, 'key': int.from_bytes(data[l:l+blen], 'big')})
                l += blen
            elif btype == 0x03:
                l += 1
                l += derparser(data[l:l+blen], blen-1)
            elif btype == 0x06:
                l+=blen
        return l

    with open(pemfile, 'r') as f:
        pem = f.read().strip()
    b64 = re.sub('-.+', '', pem).replace('\n','')
    der = base64.b64decode(b64.encode('ascii'))
    derparser(der, len(der))
    key = {}
    if len(pkey) == 9:
        key['type'] = 'pem'
        key['size'] = pkey[1]['size'] - 1
        key['modulus'] = pkey[1]['key']
        key['pubExp'] = pkey[2]['key']
        key['privExp'] = pkey[3]['key']
        key['p'] = pkey[4]['key']
        key['q'] = pkey[5]['key']
        key['e1'] = pkey[6]['key']
        key['e2'] = pkey[7]['key']
        key['coeff'] = pkey[8]['key']
    elif len(pkey) == 2:
        key['type'] = 'pub'
        key['size'] = pkey[0]['size'] - 1
        key['modulus'] = pkey[0]['key']
        key['pubExp'] = pkey[1]['key']
    return key

def encrypt(text, modulus, size, pubExp):
    """Encrypt message with public key"""
    import random
    minpsize = 8
    sectorsize = size - 3 - minpsize
    output = b''
    for i in range(0, len(text), sectorsize):
        stext = text[i: i + sectorsize]
        psize = size - 3 - len(stext)
        padding = random.getrandbits(psize*8*2).to_bytes(psize*2, 'big').replace(b'\x00', b'')
        ptext = b'\x00\x02' + padding[:psize] + b'\x00' + stext
        aux1 = int.from_bytes(ptext, 'big')
        assert aux1 < modulus
        aux2 = pow(aux1, pubExp, modulus)
        output += aux2.to_bytes(size, 'big')
    return output

def decrypt(text, modulus, size, privExp, p, q, e1, e2, coeff):
    """Decrypt message with private key
    using the Chinese Remainder Theorem"""
    output = b''
    for i in range(0, len(text), size):
        aux3 = int.from_bytes(text[i: i + size],'big')
        assert aux3 < modulus
        m1 = pow(aux3, e1, p)
        m2 = pow(aux3, e2, q)
        h = (coeff * (m1 - m2)) % p
        aux4 = m2 + h * q
        output += re.sub(b'\x00\x02[\x01-\xff]+?\x00', b'', aux4.to_bytes(size, 'big'), 1)
    return output

def slowdecrypt(text, modulus, size, privExp):
    """Decrypt message with private key"""
    output = b''
    for i in range(0, len(text), size):
        aux1 = int.from_bytes(text[i: i + size],'big')
        assert aux1 < modulus
        aux2 = pow(aux1, privExp, modulus)
        output += re.sub(b'\x00\x02[\x01-\xff]+?\x00', b'', aux2.to_bytes(size, 'big'), 1)
    return output

if len(sys.argv) != 3:
    print("specify private rsa key file and mac address as argument")
    sys.exit(0)

mac = sys.argv[2]
key = pem(sys.argv[1])

if key['type'] == 'pem':
    #classic encrypt with public and decrypt with private key pair:
    #print('text     ',mac)
    #e = encrypt(mac.encode(), key['modulus'], key['size'], key['pubExp'])
    #print('encrypted',binascii.b2a_hex(e))
    #d = decrypt(e, key['modulus'], key['size'], key['privExp'], key['p'], key['q'], key['e1'], key['e2'], key['coeff'])
    #print('decrypted',d.decode())
    #d = slowdecrypt(e, key['modulus'], key['size'], key['privExp'])
    #print('decrypted',d.decode())

    #encrypt with private key(keygen), so everybody can decrypt message(check):
    e = encrypt(mac.replace(':', '').encode(), key['modulus'], key['size'], key['privExp'])
    print('encrypted',binascii.b2a_hex(e))

    #simplified keygen:
    msg = int(mac.replace(':', ''), 16)
    coded = pow(msg, key['privExp'], key['modulus'])
    print(coded)
elif key['type'] == 'pub':
    #decrypt with pubkey(for check):
    try:
        d = slowdecrypt(binascii.a2b_hex(mac), key['modulus'], key['size'], key['pubExp'])
        print('decrypted',d.decode())
    except:
        pass

    #simplified lic decode:
    try:
        msg = int(mac)
        decoded = pow(msg, key['pubExp'], key['modulus'])
        print(binascii.b2a_hex((decoded).to_bytes(6,'big')))
    except:
        pass
