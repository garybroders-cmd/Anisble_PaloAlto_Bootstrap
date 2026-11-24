#!/usr/bin/env python3

"""
bootstrap_from_firewalls.py

Reads:
    master_paloalto.xlsm

Worksheets:
    Firewalls
    Site_Details

Generates:
    bootstrap/<hostname>.cfg

Purpose:
    Generate Palo Alto bootstrap configuration files.

Features:
    - Sets hostname
    - Configures static management IP
    - Configures DNS
    - Configures NTP
    - Enables HTTPS management
    - Enables SSH management
    - Disables HTTP
    - Disables Telnet
    - Enables password complexity
    - Creates local administrator accounts
    - Prompts for passwords during configuration load
    - Does NOT store passwords in Excel
    - Does NOT generate password hashes
"""

import os
import pandas as pd

WORKBOOK = "master_paloalto.xlsm"
OUTPUT_DIR = "bootstrap"

os.makedirs(OUTPUT_DIR, exist_ok=True)

CIDR_MASKS = {
    8: "255.0.0.0",
    16: "255.255.0.0",
    24: "255.255.255.0",
    25: "255.255.255.128",
    26: "255.255.255.192",
    27: "255.255.255.224",
    28: "255.255.255.240",
    29: "255.255.255.248",
    30: "255.255.255.252",
    31: "255.255.255.254",
    32: "255.255.255.255"
}


def clean(value):
    if pd.isna(value):
        return ""

    value = str(value).strip()

    if value.lower() == "nan":
        return ""

    return value


def cidr_to_mask(cidr):
    try:
        return CIDR_MASKS[int(cidr)]
    except Exception:
        return "255.255.255.0"


print("================================")
print("Reading workbook")
print("================================")

firewalls = pd.read_excel(
    WORKBOOK,
    sheet_name="Firewalls",
    engine="openpyxl"
)

site_details = pd.read_excel(
    WORKBOOK,
    sheet_name="Site_Details",
    engine="openpyxl"
)

generated_files = []

for _, firewall in firewalls.iterrows():

    hostname = clean(
        firewall.get("hostname")
    )

    if not hostname:
        continue

    mgmt_ip = clean(
        firewall.get("mgmt_ip")
    )

    mgmt_mask = firewall.get(
        "mgmt_mask",
        24
    )

    mgmt_gateway = clean(
        firewall.get("mgmt_gateway")
    )

    dns1 = clean(
        firewall.get("dns1")
    )

    dns2 = clean(
        firewall.get("dns2")
    )

    ntp1 = clean(
        firewall.get("ntp1")
    )

    ntp2 = clean(
        firewall.get("ntp2")
    )

    netmask = cidr_to_mask(
        mgmt_mask
    )

    cfg = []

    #
    # CLI MODE
    #
    cfg.append(
        "set cli config-output-format set"
    )

    cfg.append(
        "configure"
    )

    cfg.append("")

    #
    # HOSTNAME
    #
    cfg.append(
        f"set deviceconfig system hostname {hostname}"
    )

    cfg.append("")

    #
    # REMOVE DHCP CLIENT
    #
    cfg.append(
        "delete deviceconfig system type dhcp-client"
    )

    cfg.append("")

    #
    # STATIC MANAGEMENT
    #
    cfg.append(
        "set deviceconfig system type static"
    )

    if mgmt_ip:
        cfg.append(
            f"set deviceconfig system ip-address {mgmt_ip}"
        )

    cfg.append(
        f"set deviceconfig system netmask {netmask}"
    )

    if mgmt_gateway:
        cfg.append(
            f"set deviceconfig system default-gateway {mgmt_gateway}"
        )

    cfg.append("")

    #
    # DNS
    #
    if dns1:
        cfg.append(
            f"set deviceconfig system dns-setting servers primary {dns1}"
        )

    if dns2:
        cfg.append(
            f"set deviceconfig system dns-setting servers secondary {dns2}"
        )

    cfg.append("")

    #
    # NTP
    #
    if ntp1:
        cfg.append(
            f"set deviceconfig system ntp-servers primary-ntp-server ntp-server-address {ntp1}"
        )

    if ntp2:
        cfg.append(
            f"set deviceconfig system ntp-servers secondary-ntp-server ntp-server-address {ntp2}"
        )

    cfg.append("")

    #
    # MANAGEMENT ACCESS
    #
    cfg.append(
        "set deviceconfig system service disable-http yes"
    )

    cfg.append(
        "set deviceconfig system service disable-telnet yes"
    )

    cfg.append(
        "set deviceconfig system service disable-https no"
    )

    cfg.append(
        "set deviceconfig system service disable-ssh no"
    )

    cfg.append("")

    #
    # PASSWORD COMPLEXITY
    #
    cfg.append(
        "set mgt-config password-complexity enabled yes"
    )

    cfg.append(
        "set mgt-config password-complexity minimum-length 8"
    )

    cfg.append("")

    #
    # LOCAL ADMINISTRATORS
    #
    host_users = site_details[
        site_details["hostname"]
        .astype(str)
        .str.strip()
        == hostname
    ]

    for _, user in host_users.iterrows():

        username = clean(
            user.get("Global_Admin_User")
        )

        if not username:
            continue

        role = clean(
            user.get("role-based")
        )

        if not role:
            role = "superuser"

        #
        # Create account
        #
        cfg.append(
            f"set mgt-config users {username} permissions role-based {role} yes"
        )

        #
        # Prompt for password
        #
        cfg.append(
            f"set mgt-config users {username} password"
        )

        cfg.append("")

    #
    # COMMIT
    #
    cfg.append("commit")
    cfg.append("exit")

    output_file = os.path.join(
        OUTPUT_DIR,
        f"{hostname}.cfg"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as fh:
        fh.write(
            "\n".join(cfg)
        )

    generated_files.append(
        output_file
    )

    print(
        f"Created {output_file}"
    )

print("")
print("================================")
print("Bootstrap files generated")
print("================================")

for file in generated_files:
    print(file)

print("")
print("Example output:")
print("")
print("set cli config-output-format set")
print("configure")
print("set mgt-config users ansible permissions role-based superuser yes")
print("set mgt-config users ansible password")
print("commit")
print("exit")
print("")
print("Passwords are entered interactively by PAN-OS and are not stored in Excel or generated files.")
