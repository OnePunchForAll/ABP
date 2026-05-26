def even_parity(byte: int) -> bool:
    if not 0 <= byte <= 255:
        raise ValueError("Invalid byte")
    return bin(byte).count('1') % 2 == 0

def odd_parity(byte: int) -> bool:
    if not 0 <= byte <= 255:
        raise ValueError("Invalid byte")
    return bin(byte).count('1') % 2 != 0

def xor_parity(byte: int) -> int:
    if not 0 <= byte <= 255:
        raise ValueError("Invalid byte")
    parity = 0
    while byte:
        parity ^= byte & 1
        byte >>= 1
    return parity

def flip_bit(byte: int, bit_index: int) -> int:
    if not 0 <= byte <= 255:
        raise ValueError("Invalid byte")
    if not 0 <= bit_index <= 7:
        raise ValueError("Invalid bit index")
    return byte ^ (1 << bit_index)

def count_ones(byte: int) -> int:
    if not 0 <= byte <= 255:
        raise ValueError("Invalid byte")
    return bin(byte).count('1')
