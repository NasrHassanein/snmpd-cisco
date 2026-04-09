# Cisco IOS SNMP Simulator

Docker container running Net-SNMP's `snmpd` configured to impersonate a **Cisco ISR 4331** router running **IOS XE 16.6.2**.

Uses MIBs from [cisco/cisco-mibs](https://github.com/cisco/cisco-mibs) and a `pass_persist` Python script to serve Cisco-proprietary OID subtrees with realistic (and partially dynamic) values.

## What it simulates

| MIB / Area              | OID Subtree               | Data                                      |
|-------------------------|---------------------------|-------------------------------------------|
| MIB-II System           | `.1.3.6.1.2.1.1`          | sysDescr, sysObjectID, sysName, etc.      |
| IF-MIB                  | `.1.3.6.1.2.1.2`          | Linux interfaces renamed to Cisco style   |
| ENTITY-MIB              | `.1.3.6.1.2.1.47`         | Chassis, module, port inventory            |
| OLD-CISCO-SYSTEM-MIB    | `.1.3.6.1.4.1.9.2.1`      | Bootstrap, hostname, domain               |
| CISCO-ENVMON-MIB        | `.1.3.6.1.4.1.9.9.13`     | Temperature, fans, PSU status             |
| CISCO-PROCESS-MIB       | `.1.3.6.1.4.1.9.9.109`    | CPU utilisation (dynamic, randomised)     |
| CISCO-MEMORY-POOL-MIB   | `.1.3.6.1.4.1.9.9.48`     | Processor & I/O memory (dynamic)          |
| CISCO-FLASH-MIB         | `.1.3.6.1.4.1.9.9.10`     | Flash device size                         |

CPU, memory and temperature values fluctuate on each poll to simulate a live device.

## Quick start

```bash
# Build
docker build -t cisco-snmp-sim .

# Run
docker run -d --name cisco-router -p 10161:161/udp cisco-snmp-sim
```

Or with docker compose:

```bash
docker compose up -d
```

## SNMP credentials

### SNMPv1 / v2c

| Community string | Access |
|-----------------|--------|
| `public` | read-only |

### SNMPv3

All users share the same auth/priv password: **`1234567890abcdef`**

#### Users without context

| Username | Security level | Auth protocol | Priv protocol |
|----------|---------------|---------------|---------------|
| `user1`  | noAuthNoPriv  | —             | —             |
| `user2`  | authNoPriv    | MD5           | —             |
| `user3`  | authNoPriv    | SHA           | —             |
| `user4`  | authPriv      | MD5           | DES           |
| `user5`  | authPriv      | SHA           | DES           |
| `user6`  | authPriv      | MD5           | AES           |
| `user7`  | authPriv      | SHA           | AES           |

#### Users with named contexts

| Username | Security level | Auth protocol | Priv protocol | Context name |
|----------|---------------|---------------|---------------|--------------|
| `user11` | noAuthNoPriv  | —             | —             | `context11`  |
| `user12` | authNoPriv    | MD5           | —             | `context12`  |
| `user13` | authNoPriv    | SHA           | —             | `context13`  |
| `user14` | authPriv      | MD5           | DES           | `context14`  |
| `user15` | authPriv      | SHA           | DES           | `context15`  |

## Test commands

### SNMPv1 / v2c

```bash
snmpget  -v2c -c public localhost:10161 sysDescr.0
snmpget  -v2c -c public localhost:10161 sysObjectID.0
snmpwalk -v2c -c public localhost:10161 .1.3.6.1.4.1.9.9.13   # ENVMON
snmpwalk -v2c -c public localhost:10161 .1.3.6.1.4.1.9.9.109  # CPU
snmpwalk -v2c -c public localhost:10161 .1.3.6.1.4.1.9.9.48   # Memory
snmpwalk -v2c -c public localhost:10161 .1.3.6.1.2.1.47       # Entity
```

### SNMPv3 — noAuthNoPriv

```bash
snmpget -v3 -u user1 -l noAuthNoPriv \
    localhost:10161 sysDescr.0
```

### SNMPv3 — authNoPriv (MD5)

```bash
snmpget -v3 -u user2 -l authNoPriv \
    -a MD5 -A 1234567890abcdef \
    localhost:10161 sysDescr.0
```

### SNMPv3 — authNoPriv (SHA)

```bash
snmpget -v3 -u user3 -l authNoPriv \
    -a SHA -A 1234567890abcdef \
    localhost:10161 sysDescr.0
```

### SNMPv3 — authPriv (MD5 + DES)

```bash
snmpget -v3 -u user4 -l authPriv \
    -a MD5 -A 1234567890abcdef \
    -x DES -X 1234567890abcdef \
    localhost:10161 sysDescr.0
```

### SNMPv3 — authPriv (SHA + DES)

```bash
snmpget -v3 -u user5 -l authPriv \
    -a SHA -A 1234567890abcdef \
    -x DES -X 1234567890abcdef \
    localhost:10161 sysDescr.0
```

### SNMPv3 — authPriv (MD5 + AES)

```bash
snmpget -v3 -u user6 -l authPriv \
    -a MD5 -A 1234567890abcdef \
    -x AES -X 1234567890abcdef \
    localhost:10161 sysDescr.0
```

### SNMPv3 — authPriv (SHA + AES)

```bash
snmpget -v3 -u user7 -l authPriv \
    -a SHA -A 1234567890abcdef \
    -x AES -X 1234567890abcdef \
    localhost:10161 sysDescr.0
```

### SNMPv3 — with named context

```bash
# noAuthNoPriv + context
snmpget -v3 -u user11 -l noAuthNoPriv \
    -n context11 \
    localhost:10161 sysDescr.0

# authNoPriv (MD5) + context
snmpget -v3 -u user12 -l authNoPriv \
    -a MD5 -A 1234567890abcdef \
    -n context12 \
    localhost:10161 sysDescr.0

# authPriv (MD5 + DES) + context
snmpget -v3 -u user14 -l authPriv \
    -a MD5 -A 1234567890abcdef \
    -x DES -X 1234567890abcdef \
    -n context14 \
    localhost:10161 sysDescr.0
```

### SNMPv3 — walk Cisco enterprise OIDs

```bash
snmpwalk -v3 -u user7 -l authPriv \
    -a SHA -A 1234567890abcdef \
    -x AES -X 1234567890abcdef \
    localhost:10161 .1.3.6.1.4.1.9.9.13   # ENVMON

snmpwalk -v3 -u user7 -l authPriv \
    -a SHA -A 1234567890abcdef \
    -x AES -X 1234567890abcdef \
    localhost:10161 .1.3.6.1.4.1.9.9.109  # CPU

snmpwalk -v3 -u user7 -l authPriv \
    -a SHA -A 1234567890abcdef \
    -x AES -X 1234567890abcdef \
    localhost:10161 .1.3.6.1.2.1.47       # Entity
```

## Customising the device identity

Edit `snmpd.conf` and change:

- **sysDescr** — the full IOS version banner
- **sysObjectID** — look up your target device in `CISCO-PRODUCTS-MIB.my`:
  ```bash
  grep -i "catalyst3750\|ciscoASR\|ciscoISR" v2/CISCO-PRODUCTS-MIB.my
  ```
- **sysName / sysLocation / sysContact** — whatever you need

To simulate a different platform's proprietary OIDs, edit the `OID_MAP` dictionary in `cisco_fake_agent.py`.


## Extending OID coverage

1. Identify the MIBs your NMS expects by checking the [support lists](https://github.com/cisco/cisco-mibs/tree/main/supportlists) for your target device
2. Add OID entries to the `OID_MAP` dict in `cisco_fake_agent.py`
3. For dynamic values, use a callable (function) as the value — it gets invoked on every SNMP poll
4. Rebuild or restart the container

## Architecture

```
┌────────────┐         ┌─────────────────────────────────┐
│  NMS / CLI │  SNMP   │  Docker Container               │
│  snmpget   │ ──────► │                                 │
│  snmpwalk  │  :161   │  snmpd                          │
│  LibreNMS  │ ◄────── │   ├─ override: sysDescr, etc.   │
│  Zabbix    │         │   ├─ IF-MIB (Linux real ifaces) │
│  Nagios    │         │   └─ pass_persist ──► python3   │
└────────────┘         │       cisco_fake_agent.py       │
                       │       (Cisco enterprise OIDs)   │
                       └─────────────────────────────────┘
```
