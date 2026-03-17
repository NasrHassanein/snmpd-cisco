#!/usr/bin/env python3
"""
pass_persist script for faking Cisco IOS proprietary SNMP OIDs.
Handles GET, GETNEXT, and PING requests from snmpd.

Simulates a Cisco ISR 4331 router with:
  - OLD-CISCO-SYSTEM-MIB (local system info)
  - CISCO-ENVMON-MIB (temperature, fans, PSUs)
  - CISCO-MEMORY-POOL-MIB (memory stats)
  - CISCO-PROCESS-MIB (CPU utilisation)
  - CISCO-FLASH-MIB (flash filesystem)
  - ENTITY-MIB physical table entries
"""

import sys
import time
import random

# ---------------------------------------------------------------------------
# Helper: dynamic value generators
# ---------------------------------------------------------------------------
_start = time.time()

def _uptime():
    """Hundredths of a second since start."""
    return str(int((time.time() - _start) * 100))

def _cpu_5sec():
    return str(random.randint(2, 12))

def _cpu_1min():
    return str(random.randint(3, 10))

def _cpu_5min():
    return str(random.randint(2, 8))

def _mem_used():
    return str(random.randint(180_000_000, 220_000_000))

def _mem_free():
    return str(random.randint(300_000_000, 340_000_000))

def _temperature():
    return str(random.randint(30, 42))

# ---------------------------------------------------------------------------
# OID table: OID -> (type, value_or_callable)
# If the value is callable it is invoked on every request (dynamic data).
# ---------------------------------------------------------------------------
OID_MAP = {
    # === OLD-CISCO-SYSTEM-MIB (.1.3.6.1.4.1.9.2.1) ===
    ".1.3.6.1.4.1.9.2.1.1.0":  ("string",   "System Bootstrap, Version 16.6(2r), RELEASE SOFTWARE (fc1)"),
    ".1.3.6.1.4.1.9.2.1.2.0":  ("string",   "reload"),
    ".1.3.6.1.4.1.9.2.1.3.0":  ("string",   "router-gw-01"),
    ".1.3.6.1.4.1.9.2.1.4.0":  ("string",   "example.com"),
    ".1.3.6.1.4.1.9.2.1.56.0": ("string",   "flash:isr4300-universalk9.16.06.02.SPA.bin"),
    ".1.3.6.1.4.1.9.2.1.73.0": ("string",   "router-gw-01.example.com"),

    # === CISCO-PROCESS-MIB — CPU utilisation (.1.3.6.1.4.1.9.9.109) ===
    # cpmCPUTotalTable entry index 1
    ".1.3.6.1.4.1.9.9.109.1.1.1.1.3.1":  ("gauge", _cpu_5sec),   # cpmCPUTotal5sec
    ".1.3.6.1.4.1.9.9.109.1.1.1.1.4.1":  ("gauge", _cpu_1min),   # cpmCPUTotal1min
    ".1.3.6.1.4.1.9.9.109.1.1.1.1.5.1":  ("gauge", _cpu_5min),   # cpmCPUTotal5min

    # === CISCO-MEMORY-POOL-MIB (.1.3.6.1.4.1.9.9.48) ===
    # Processor memory pool (index 1)
    ".1.3.6.1.4.1.9.9.48.1.1.1.2.1":  ("string",  "Processor"),
    ".1.3.6.1.4.1.9.9.48.1.1.1.5.1":  ("gauge",   _mem_used),    # ciscoMemoryPoolUsed
    ".1.3.6.1.4.1.9.9.48.1.1.1.6.1":  ("gauge",   _mem_free),    # ciscoMemoryPoolFree
    ".1.3.6.1.4.1.9.9.48.1.1.1.7.1":  ("gauge",   "0"),          # ciscoMemoryPoolLargestFree
    # I/O memory pool (index 2)
    ".1.3.6.1.4.1.9.9.48.1.1.1.2.2":  ("string",  "I/O"),
    ".1.3.6.1.4.1.9.9.48.1.1.1.5.2":  ("gauge",   "12582912"),
    ".1.3.6.1.4.1.9.9.48.1.1.1.6.2":  ("gauge",   "20971520"),
    ".1.3.6.1.4.1.9.9.48.1.1.1.7.2":  ("gauge",   "0"),

    # === CISCO-ENVMON-MIB (.1.3.6.1.4.1.9.9.13) ===
    # Temperature sensors
    ".1.3.6.1.4.1.9.9.13.1.3.1.2.1":  ("string",  "Chassis Temperature Sensor"),
    ".1.3.6.1.4.1.9.9.13.1.3.1.3.1":  ("gauge",   _temperature),  # current value
    ".1.3.6.1.4.1.9.9.13.1.3.1.4.1":  ("integer",  "55"),          # threshold
    ".1.3.6.1.4.1.9.9.13.1.3.1.6.1":  ("integer",  "1"),           # state: normal(1)
    ".1.3.6.1.4.1.9.9.13.1.3.1.2.2":  ("string",  "CPU Temperature Sensor"),
    ".1.3.6.1.4.1.9.9.13.1.3.1.3.2":  ("gauge",   _temperature),
    ".1.3.6.1.4.1.9.9.13.1.3.1.4.2":  ("integer",  "75"),
    ".1.3.6.1.4.1.9.9.13.1.3.1.6.2":  ("integer",  "1"),

    # Fan sensors
    ".1.3.6.1.4.1.9.9.13.1.4.1.2.1":  ("string",  "Fan 1"),
    ".1.3.6.1.4.1.9.9.13.1.4.1.3.1":  ("integer",  "1"),  # normal
    ".1.3.6.1.4.1.9.9.13.1.4.1.2.2":  ("string",  "Fan 2"),
    ".1.3.6.1.4.1.9.9.13.1.4.1.3.2":  ("integer",  "1"),

    # Power supply
    ".1.3.6.1.4.1.9.9.13.1.5.1.2.1":  ("string",  "Power Supply 1"),
    ".1.3.6.1.4.1.9.9.13.1.5.1.3.1":  ("integer",  "1"),  # normal
    ".1.3.6.1.4.1.9.9.13.1.5.1.4.1":  ("string",  "AC Power Supply"),

    # === CISCO-FLASH-MIB (.1.3.6.1.4.1.9.9.10) ===
    ".1.3.6.1.4.1.9.9.10.1.1.4.1.1.1.1": ("integer", "1"),              # device index
    ".1.3.6.1.4.1.9.9.10.1.1.4.1.1.5.1": ("gauge",   "2097152000"),     # size (2 GB)
    ".1.3.6.1.4.1.9.9.10.1.1.4.1.1.6.1": ("gauge",   "1258291200"),     # free

    # === ENTITY-MIB entPhysicalTable (.1.3.6.1.2.1.47.1.1.1) ===
    # Chassis (index 1)
    ".1.3.6.1.2.1.47.1.1.1.1.2.1":   ("string",  "ISR4331/K9"),                 # entPhysicalDescr
    ".1.3.6.1.2.1.47.1.1.1.1.3.1":   ("objectid", ".1.3.6.1.4.1.9.12.3.1.3"),   # entPhysicalVendorType
    ".1.3.6.1.2.1.47.1.1.1.1.4.1":   ("integer",  "0"),                          # entPhysicalContainedIn
    ".1.3.6.1.2.1.47.1.1.1.1.5.1":   ("integer",  "3"),                          # class: chassis(3)
    ".1.3.6.1.2.1.47.1.1.1.1.7.1":   ("string",  "ISR4331/K9"),                 # entPhysicalName
    ".1.3.6.1.2.1.47.1.1.1.1.8.1":   ("string",  ""),                           # entPhysicalHardwareRev
    ".1.3.6.1.2.1.47.1.1.1.1.9.1":   ("string",  "16.6.2"),                     # entPhysicalFirmwareRev
    ".1.3.6.1.2.1.47.1.1.1.1.10.1":  ("string",  "16.6.2"),                     # entPhysicalSoftwareRev
    ".1.3.6.1.2.1.47.1.1.1.1.11.1":  ("string",  "FLM1234ABC0"),               # entPhysicalSerialNum
    ".1.3.6.1.2.1.47.1.1.1.1.12.1":  ("string",  "Cisco Systems, Inc."),        # entPhysicalMfgName
    ".1.3.6.1.2.1.47.1.1.1.1.13.1":  ("string",  "ISR4331/K9"),                 # entPhysicalModelName

    # Module (index 2)
    ".1.3.6.1.2.1.47.1.1.1.1.2.2":   ("string",  "ISR4331 Built-In NIM controller"),
    ".1.3.6.1.2.1.47.1.1.1.1.4.2":   ("integer",  "1"),    # contained in chassis
    ".1.3.6.1.2.1.47.1.1.1.1.5.2":   ("integer",  "9"),    # class: module(9)
    ".1.3.6.1.2.1.47.1.1.1.1.7.2":   ("string",  "NIM subslot 0/0"),
    ".1.3.6.1.2.1.47.1.1.1.1.11.2":  ("string",  "FLM1234ABC1"),
    ".1.3.6.1.2.1.47.1.1.1.1.13.2":  ("string",  "ISR4331-3x1GE"),

    # GigabitEthernet0/0/0 port (index 3)
    ".1.3.6.1.2.1.47.1.1.1.1.2.3":   ("string",  "GigabitEthernet0/0/0"),
    ".1.3.6.1.2.1.47.1.1.1.1.4.3":   ("integer",  "2"),    # contained in module
    ".1.3.6.1.2.1.47.1.1.1.1.5.3":   ("integer",  "10"),   # class: port(10)
    ".1.3.6.1.2.1.47.1.1.1.1.7.3":   ("string",  "GigabitEthernet0/0/0"),
}


# ---------------------------------------------------------------------------
# Sorted OID list for GETNEXT
# ---------------------------------------------------------------------------
def _oid_sort_key(oid):
    return tuple(int(p) for p in oid.strip('.').split('.'))

SORTED_OIDS = sorted(OID_MAP.keys(), key=_oid_sort_key)


def find_next_oid(requested):
    req_tuple = _oid_sort_key(requested)
    for oid in SORTED_OIDS:
        if _oid_sort_key(oid) > req_tuple:
            return oid
    return None


def resolve_value(entry):
    """Return (type, value_string), calling the value if it's a callable."""
    t, v = entry
    if callable(v):
        return t, v()
    return t, v


def respond(oid, snmp_type, value):
    print(oid)
    print(snmp_type)
    print(value)
    sys.stdout.flush()


def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
        except EOFError:
            break

        if not line:
            continue

        if line == "PING":
            print("PONG")
            sys.stdout.flush()
            continue

        command = line.lower()

        try:
            oid = sys.stdin.readline().strip()
        except EOFError:
            break

        if command == "get":
            if oid in OID_MAP:
                t, v = resolve_value(OID_MAP[oid])
                respond(oid, t, v)
            else:
                print("NONE")
                sys.stdout.flush()

        elif command == "getnext":
            next_oid = find_next_oid(oid)
            if next_oid:
                t, v = resolve_value(OID_MAP[next_oid])
                respond(next_oid, t, v)
            else:
                print("NONE")
                sys.stdout.flush()

        elif command == "set":
            # consume the remaining set data and reject
            sys.stdin.readline()  # type
            sys.stdin.readline()  # value
            print("not-writable")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
