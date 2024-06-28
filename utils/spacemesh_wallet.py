import hashlib
import binascii
from bech32 import bech32_encode, convertbits

def blake3_hash(data):
    return hashlib.blake3(data).digest()

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

def bech32_encode_address(address, hrp="sm"):
    """Encode address to bech32 format"""
    converted = convertbits(address, 8, 5)
    return bech32_encode(hrp, converted)

def spawn_wallet_address(public_key_hex):
    """Spawn a wallet address from a hex-encoded ED25519 public key"""
    try:
        # Convert hex string to bytes
        public_key = binascii.unhexlify(public_key_hex)
        
        # Ensure the public key is 32 bytes
        if len(public_key) != 32:
            raise ValueError("Public key must be 32 bytes long")
        
        # Compute raw address
        raw_address = compute_address(public_key)
        
        # Encode to bech32
        bech32_address = bech32_encode_address(raw_address)
        
        return {
            "raw_address": binascii.hexlify(raw_address).decode(),
            "bech32_address": bech32_address
        }
    except ValueError as e:
        return {"error": str(e)}
    except binascii.Error:
        return {"error": "Invalid hex string for public key"}

# Example usage
if __name__ == "__main__":
    # Example public key (replace with actual public key)
    public_key = "8e935bb7da33de54f58586bf2410425847b9281725fe1698be2433df3999cd01"
    
    result = spawn_wallet_address(public_key)
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Raw address: {result['raw_address']}")
        print(f"Bech32 address: {result['bech32_address']}")