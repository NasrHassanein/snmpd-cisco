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

# Test
snmpget  -v2c -c public localhost:10161 sysDescr.0
snmpget  -v2c -c public localhost:10161 sysObjectID.0
snmpwalk -v2c -c public localhost:10161 .1.3.6.1.4.1.9.9.13   # ENVMON
snmpwalk -v2c -c public localhost:10161 .1.3.6.1.4.1.9.9.109  # CPU
snmpwalk -v2c -c public localhost:10161 .1.3.6.1.4.1.9.9.48   # Memory
snmpwalk -v2c -c public localhost:10161 .1.3.6.1.2.1.47       # Entity
```

Or with docker compose:

```bash
docker compose up -d
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
