import os
from coincurve import PrivateKey
from bech32 import bech32_encode, convertbits

def generate_spacemesh_address():
    private_key = PrivateKey(os.urandom(32))
    public_key = private_key.public_key.format(compressed=True)
    data = convertbits(public_key, 8, 5)
    address = bech32_encode("sm", data)
    return address

def validate_spacemesh_address(address):
    return address.startswith("sm1") and len(address) == 43