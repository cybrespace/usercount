#!/usr/bin/python3

import sys

def fw(c):
    if (c == ' '): return chr(0x3000)
    return chr(ord(c) - 0x20 + 0xFF00) if (0x21 <= ord(c) <= 0x7e) else c

def fullwidth(s):
    return "".join([fw(c) for c in s])

if __name__ == "__main__":
    print(" ".join([fullwidth(s) for s in sys.argv[1:]]))
