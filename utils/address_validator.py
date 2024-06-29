from bech32 import bech32_decode, convertbits

def validate_spacemesh_address(address):
    """Validate a Spacemesh address."""
    # Check if the address starts with "sm1" and has the correct length
    if not address.startswith("sm1") or len(address) != 43:
        return False

    # Decode the bech32 address
    hrp, data = bech32_decode(address)
    
    # Check if the human-readable part is "sm"
    if hrp != "sm":
        return False

    # Convert the data from base32 to bytes
    decoded = convertbits(data, 5, 8, False)
    
    # Check if the conversion was successful and the result has the correct length
    if decoded is None or len(decoded) != 24:
        return False

    # Verify that the first 4 bytes are zero
    if any(decoded[:4]):
        return False

    # All checks passed, the address is valid
    return True