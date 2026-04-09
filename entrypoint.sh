#!/bin/bash
set -e

echo "=== Cisco SNMP Simulator (ISR 4331) ==="
echo "  sysDescr    : Cisco IOS XE 16.6.2"
echo "  sysObjectID : .1.3.6.1.4.1.9.1.2458"
echo "  Community   : public"
echo "  Port        : 161/udp"
echo "  SNMPv3 users: user1-user7, user11-user15"
echo "  SNMPv3 pass : 1234567890abcdef"
echo "========================================="

# ─── Create SNMPv3 users (MIMIC Viewer defaults) ─────────────────────────────
# createUser directives must be in the file snmpd actually reads (-c flag).
# snmpd processes them at startup, hashes the passwords, and writes usmUser
# entries to the persistent store (/var/lib/snmp). The directory must exist
# and be writable before snmpd starts.
mkdir -p /var/lib/snmp
cat >> /etc/snmp/snmpd.conf <<'EOF'

# ─── SNMPv3 createUser (appended by entrypoint) ──────────────────────────────
# SNMPv3 users — MIMIC Viewer defaults (password: 1234567890abcdef)

# Users without context names
createUser user1
createUser user2 MD5 1234567890abcdef
createUser user3 SHA 1234567890abcdef
createUser user4 MD5 1234567890abcdef DES 1234567890abcdef
createUser user5 SHA 1234567890abcdef DES 1234567890abcdef
createUser user6 MD5 1234567890abcdef AES 1234567890abcdef
createUser user7 SHA 1234567890abcdef AES 1234567890abcdef

# Users with context names
createUser user11
createUser user12 MD5 1234567890abcdef
createUser user13 SHA 1234567890abcdef
createUser user14 MD5 1234567890abcdef DES 1234567890abcdef
createUser user15 SHA 1234567890abcdef DES 1234567890abcdef
EOF

# Start snmpd in foreground, log to stderr
exec /usr/sbin/snmpd -f -Lo -C -c /etc/snmp/snmpd.conf
