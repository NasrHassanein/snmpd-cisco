###############################################################################
# Dockerfile — Cisco IOS SNMP Simulator
#
# Builds a container running Net-SNMP's snmpd configured to impersonate
# a Cisco ISR 4331 router (IOS XE 16.6.2).
#
# Uses MIBs from https://github.com/cisco/cisco-mibs and a pass_persist
# Python script to serve Cisco-proprietary OID subtrees.
#
# Build:
#   docker build -t cisco-snmp-sim .
#
# Run:
#   docker run -d --name cisco-router -p 10161:161/udp cisco-snmp-sim
#
# Test:
#   snmpget  -v2c -c public localhost:10161 sysDescr.0
#   snmpwalk -v2c -c public localhost:10161 .1.3.6.1.4.1.9.9.13
#   snmpwalk -v2c -c public localhost:10161 .1.3.6.1.2.1.47
###############################################################################

FROM ubuntu:24.04

LABEL maintainer="snmp-sim"
LABEL description="Cisco IOS SNMP simulator using Net-SNMP + cisco/cisco-mibs"

ENV DEBIAN_FRONTEND=noninteractive

# ─── 1. Install packages ────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        snmpd \
        snmp \
        libsnmp-dev \
        snmp-mibs-downloader \
        python3 \
        git \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Download standard IETF/IANA MIBs
RUN download-mibs 2>/dev/null || true

# ─── 2. Clone Cisco MIBs and install them ───────────────────────────────────
RUN git clone --depth 1 https://github.com/cisco/cisco-mibs.git /tmp/cisco-mibs \
    && mkdir -p /usr/share/snmp/mibs/cisco \
    && cp /tmp/cisco-mibs/v2/*.my /usr/share/snmp/mibs/cisco/ \
    && rm -rf /tmp/cisco-mibs

# ─── 3. Client-side MIB config (enables MIB name resolution) ────────────────
COPY snmp.conf /etc/snmp/snmp.conf

# ─── 4. snmpd configuration with Cisco identity overrides ───────────────────
COPY snmpd.conf /etc/snmp/snmpd.conf

# ─── 5. pass_persist agent script ───────────────────────────────────────────
COPY cisco_fake_agent.py /usr/local/bin/cisco_fake_agent.py
RUN chmod +x /usr/local/bin/cisco_fake_agent.py

# ─── 6. Entrypoint ─────────────────────────────────────────────────────────
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 161/udp

CMD ["/entrypoint.sh"]
