import hashlib
import binascii
import blake3
from bech32 import bech32_encode, convertbits
from config import NETWORK_CONFIG, BOT_PUBKEY
import base58
from bip_utils import Bip44, Bip44Coins, Bip44Changes

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

def get_wallet_index(discord_id):
    """Generate a deterministic index from a Discord ID"""
    # Convert Discord ID to bytes
    id_bytes = str(discord_id).encode()
    
    # Hash the Discord ID
    hash_object = hashlib.sha256(id_bytes)
    hash_hex = hash_object.hexdigest()
    
    # Take the last 8 characters (4 bytes) of the hex string and convert to int
    # Then use modulo to ensure it's within the valid range for BIP44
    return int(hash_hex[-8:], 16) % (2**31)

def spawn_wallet_address(discord_id):
    """Generate a Spacemesh address using HD wallet derivation based on Discord ID"""
    try:
        # Use BOT_PUBKEY as the seed (you might want to use a more secure method in production)
        seed_bytes = base58.b58decode(BOT_PUBKEY)
        
        # Get the wallet index from the Discord ID
        wallet_index = get_wallet_index(discord_id)
        
        # Create a BIP44 object (we're using Ethereum derivation path as Spacemesh doesn't have its own yet)
        bip44_mst_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
        
        # Derive the child key
        bip44_acc_ctx = bip44_mst_ctx.Purpose().Coin().Account(0)
        bip44_chg_ctx = bip44_acc_ctx.Change(Bip44Changes.CHAIN_EXT)
        bip44_addr_ctx = bip44_chg_ctx.AddressIndex(wallet_index)
        
        # Get the public key from the derived key
        public_key_bytes = bip44_addr_ctx.PublicKey().RawCompressed().ToBytes()
        
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
def test_spawn_wallet_address():
    # Test with some sample Discord IDs
    test_ids = [170855291636809728, 534770838524919829, 123456789012345678, 987654321098765432]
    
    for discord_id in test_ids:
        address = spawn_wallet_address(discord_id)
        print(f"Discord ID: {discord_id}")
        print(f"Generated Spacemesh address: {address}")
        print(f"Wallet Index: {get_wallet_index(discord_id)}")
        print()

if __name__ == "__main__":
    test_spawn_wallet_address()