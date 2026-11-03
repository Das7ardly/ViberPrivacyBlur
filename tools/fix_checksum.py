"""Set a valid PE checksum on the built exe.

PyInstaller leaves the PE checksum as 0, which some AV engines treat as a
suspicious signal. Recomputing it is a known, safe mitigation.
Usage: python fix_checksum.py <path-to-exe>
"""
import sys
import pefile

path = sys.argv[1]
pe = pefile.PE(path)
old = pe.OPTIONAL_HEADER.CheckSum
pe.OPTIONAL_HEADER.CheckSum = pe.generate_checksum()
pe.write(path)
new = pe.OPTIONAL_HEADER.CheckSum
pe.close()
print(f"checksum: {hex(old)} -> {hex(new)}")
