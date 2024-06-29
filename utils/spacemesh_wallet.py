import hashlib
import binascii
import blake3
from bech32 import bech32_encode, convertbits
from config import NETWORK_CONFIG, BOT_PUBKEY
import base58

def blake3_hash(data):
    return blake3.blake3(data).digest()

def compute_address(public_key):
    # Wallet template address
    template = b'\x00' * 23 + b'\x01'
    
    # Concatenate template and public key
    data = template + public_key
    
    # Hash using BLAKE3
    hashed = blake3_hash(data)
    
    # Take last 20 bytes and prefix with 0x00000000
    address = b'\x00' * 4 + hashed[-20:]
    
    return address

def bech32_encode_address(address, hrp=NETWORK_CONFIG['HRP']):
    """Encode address to bech32 format"""
    converted = convertbits(address, 8, 5)
    return bech32_encode(hrp, converted)

def spawn_wallet_address():
    """Generate a Spacemesh address from the bot's public key"""
    try:
        # Decode the bot's public key from base58
        public_key_bytes = base58.b58decode(BOT_PUBKEY)
        
        # Ensure the public key is 32 bytes
        if len(public_key_bytes) != 32:
            raise ValueError("Public key must be 32 bytes long")
        
        # Compute raw address
        raw_address = compute_address(public_key_bytes)
        
        # Encode to bech32
        bech32_address = bech32_encode_address(raw_address)
        
        return bech32_address
    except ValueError as e:
        return f"Error: {str(e)}"
    except binascii.Error:
        return "Error: Invalid public key format"
    except Exception as e:
        return f"Error: An unexpected error occurred - {str(e)}"

# Test function
if __name__ == "__main__":
    address = spawn_wallet_address()
    print(f"Generated Spacemesh address: {address}")