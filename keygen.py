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

mac = sys.argv[2]
key = pem(sys.argv[1])

if key['type'] == 'pem':
    #simplified keygen:
    msg = int(mac.replace(':', ''), 16)
    coded = pow(msg, key['privExp'], key['modulus'])
    print(coded)
elif key['type'] == 'pub':
    msg = int(mac)
    decoded = pow(msg, key['pubExp'], key['modulus'])
    print(binascii.b2a_hex((decoded).to_bytes(6,'big')))
