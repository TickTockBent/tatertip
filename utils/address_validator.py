from bech32 import bech32_decode, convertbits

def validate_spacemesh_address(address):
    """Validate a Spacemesh address."""
    print(f"Validating address: {address}")
    
    # Check if the address starts with "sm1" and has the correct length
    if not address.startswith("sm1") or len(address) != 43:
        print(f"Invalid prefix or length. Prefix: {address[:3]}, Length: {len(address)}")
        return False
    print("Prefix and length check passed")

    # Decode the bech32 address
    hrp, data = bech32_decode(address)
    print(f"Decoded HRP: {hrp}, Data length: {len(data) if data else 'None'}")
    
    # Check if the human-readable part is "sm"
    if hrp != "sm":
        print(f"Invalid HRP: {hrp}")
        return False
    print("HRP check passed")

    # Convert the data from base32 to 8-bit bytes
    decoded = convertbits(data, 5, 8, pad=False)
    print(f"Decoded data length: {len(decoded) if decoded else 'None'}")
    
    # Check if the conversion was successful and the result has the correct length
    if decoded is None or len(decoded) != 24:
        print(f"Invalid decoded length: {len(decoded) if decoded else 'None'}")
        return False
    print("Decoded length check passed")

    # Verify that the first 4 bytes are zero
    if not all(b == 0 for b in decoded[:4]):
        print(f"First 4 bytes are not zero: {decoded[:4]}")
        return False
    print("First 4 bytes zero check passed")

    # All checks passed, the address is valid
    print("All checks passed, address is valid")
    return True

# Test the function
test_address = "sm1qqqqqqyzahon8xq784hgn7nvr6dtdxf76aaatumgnefc0q"
print(f"Is valid: {validate_spacemesh_address(test_address)}")