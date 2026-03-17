#!/bin/bash
set -e

echo "=== Cisco SNMP Simulator (ISR 4331) ==="
echo "  sysDescr : Cisco IOS XE 16.6.2"
echo "  sysObjectID: .1.3.6.1.4.1.9.1.2458"
echo "  Community : public"
echo "  Port      : 161/udp"
echo "========================================="

# Start snmpd in foreground, log to stderr
exec /usr/sbin/snmpd -f -Lo -C -c /etc/snmp/snmpd.conf
