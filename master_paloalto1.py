#!/usr/bin/env python3

import pandas as pd
import yaml
from collections import defaultdict

WORKBOOK = "master_paloalto.xlsm"

# =====================================================
# LOAD WORKBOOK
# =====================================================

print("Loading workbook...")

firewalls_df = pd.read_excel(
    WORKBOOK,
    sheet_name="Firewalls"
)

interfaces_df = pd.read_excel(
    WORKBOOK,
    sheet_name="Interfaces"
)

zones_df = pd.read_excel(
    WORKBOOK,
    sheet_name="Zones"
)

# =====================================================
# ZONE LOOKUP
# =====================================================

zone_dict = {}

for _, row in zones_df.iterrows():

    zone_name = str(row["zone"]).strip()
    zone_type = str(row["type"]).strip()

    zone_dict[zone_name] = zone_type

# =====================================================
# INVENTORY
# =====================================================

inventory = []

inventory.append("[paloalto_active]")

for _, row in firewalls_df.iterrows():

    role = str(row["ha_role"]).strip()

    if role.lower() == "active":

        inventory.append(
            f"{row['hostname']} ansible_host={row['mgmt_ip']}"
        )

inventory.append("")
inventory.append("[paloalto_passive]")

for _, row in firewalls_df.iterrows():

    role = str(row["ha_role"]).strip()

    if role.lower() == "passive":

        inventory.append(
            f"{row['hostname']} ansible_host={row['mgmt_ip']}"
        )

inventory.extend([
    "",
    "[paloalto:children]",
    "paloalto_active",
    "paloalto_passive",
    "",
    "[paloalto:vars]",
    "ansible_connection=local",
    "ansible_network_os=paloaltonetworks.panos.panos"
])

with open("inventory.ini", "w") as f:

    f.write("\n".join(inventory))

print("Created inventory.ini")

# =====================================================
# INTERFACE PLAYBOOK
# =====================================================

interface_playbook = [{
    "name": "Configure Palo Alto Interfaces",
    "hosts": "paloalto",
    "gather_facts": False,
    "collections": [
        "paloaltonetworks.panos"
    ],
    "tasks": []
}]

interface_tasks = interface_playbook[0]["tasks"]

# =====================================================
# ZONE PLAYBOOK
# =====================================================

zone_playbook = [{
    "name": "Configure Palo Alto Zones",
    "hosts": "paloalto",
    "gather_facts": False,
    "collections": [
        "paloaltonetworks.panos"
    ],
    "tasks": []
}]

zone_tasks = zone_playbook[0]["tasks"]

# =====================================================
# VIRTUAL ROUTER PLAYBOOK
# =====================================================

vr_playbook = [{
    "name": "Configure Palo Alto Virtual Routers",
    "hosts": "paloalto",
    "gather_facts": False,
    "collections": [
        "paloaltonetworks.panos"
    ],
    "tasks": []
}]

vr_tasks = vr_playbook[0]["tasks"]

# =====================================================
# TRACK DUPLICATES
# =====================================================

created_zones = set()

created_vrs = set()

# =====================================================
# PROCESS INTERFACES
# =====================================================

for _, row in interfaces_df.iterrows():

    hostname = str(
        row["hostname"]
    ).strip()

    for x in range(1, 11):

        interface_col = f"interface_{x}"
        ip_col = f"ip_address_{x}"
        mask_col = f"cidr_mask_{x}"
        zone_col = f"zone_{x}"
        vr_col = f"vr_{x}"

        if interface_col not in interfaces_df.columns:
            continue

        interface = row.get(interface_col)

        if pd.isna(interface):
            continue

        interface = str(interface).strip()

        if interface == "":
            continue

        ip_address = ""

        if ip_col in interfaces_df.columns:
            value = row.get(ip_col)

            if pd.notna(value):
                ip_address = str(value).strip()

        cidr_mask = ""

        if mask_col in interfaces_df.columns:
            value = row.get(mask_col)

            if pd.notna(value):
                cidr_mask = str(value).strip()

        zone = "TRUST"

        if zone_col in interfaces_df.columns:
            value = row.get(zone_col)

            if pd.notna(value):
                zone = str(value).strip()

        virtual_router = "default"

        if vr_col in interfaces_df.columns:
            value = row.get(vr_col)

            if pd.notna(value):
                virtual_router = str(value).strip()

        # ====================================
        # INTERFACE TASK
        # ====================================

        if ip_address:

            interface_tasks.append(
                {
                    "name":
                    f"{hostname} {interface}",

                    "paloaltonetworks.panos.panos_l3_subinterface":
                    {
                        "provider":
                        "{{ provider }}",

                        "name":
                        interface,

                        "ip":
                        [
                            f"{ip_address}/{cidr_mask}"
                        ],

                        "state":
                        "present"
                    }
                }
            )

        # ====================================
        # ZONE TASK
        # ====================================

        zone_key = (
            zone,
            interface
        )

        if zone_key not in created_zones:

            zone_type = zone_dict.get(
                zone,
                "layer3"
            )

            zone_tasks.append(
                {
                    "name":
                    f"Zone {zone}",

                    "paloaltonetworks.panos.panos_zone":
                    {
                        "provider":
                        "{{ provider }}",

                        "zone":
                        zone,

                        "mode":
                        zone_type,

                        "interface":
                        [
                            interface
                        ],

                        "state":
                        "present"
                    }
                }
            )

            created_zones.add(
                zone_key
            )

        # ====================================
        # VIRTUAL ROUTER TASK
        # ====================================

        vr_key = (
            virtual_router,
            interface
        )

        if vr_key not in created_vrs:

            vr_tasks.append(
                {
                    "name":
                    f"{virtual_router} {interface}",

                    "paloaltonetworks.panos.panos_virtual_router":
                    {
                        "provider":
                        "{{ provider }}",

                        "name":
                        virtual_router,

                        "interface":
                        [
                            interface
                        ],

                        "state":
                        "present"
                    }
                }
            )

            created_vrs.add(
                vr_key
            )

# =====================================================
# COMMIT TASKS
# =====================================================

commit_task = {
    "name": "Commit Configuration",
    "paloaltonetworks.panos.panos_commit_firewall": {
        "provider": "{{ provider }}"
    }
}

interface_tasks.append(commit_task)
zone_tasks.append(commit_task)
vr_tasks.append(commit_task)

# =====================================================
# WRITE FILES
# =====================================================

with open(
    "configure_interfaces.yml",
    "w"
) as f:

    yaml.dump(
        interface_playbook,
        f,
        sort_keys=False,
        default_flow_style=False
    )

with open(
    "configure_zones.yml",
    "w"
) as f:

    yaml.dump(
        zone_playbook,
        f,
        sort_keys=False,
        default_flow_style=False
    )

with open(
    "configure_virtual_routers.yml",
    "w"
) as f:

    yaml.dump(
        vr_playbook,
        f,
        sort_keys=False,
        default_flow_style=False
    )

# =====================================================
# MASTER PLAYBOOK
# =====================================================

site_deploy = [
    {
        "import_playbook":
        "configure_interfaces.yml"
    },
    {
        "import_playbook":
        "configure_zones.yml"
    },
    {
        "import_playbook":
        "configure_virtual_routers.yml"
    }
]

with open(
    "site_deploy.yml",
    "w"
) as f:

    yaml.dump(
        site_deploy,
        f,
        sort_keys=False,
        default_flow_style=False
    )

print("================================")
print("Generated Files")
print("================================")
print("inventory.ini")
print("configure_interfaces.yml")
print("configure_zones.yml")
print("configure_virtual_routers.yml")
print("site_deploy.yml")
print("================================")
