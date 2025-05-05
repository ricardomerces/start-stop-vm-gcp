import base64
import functions_framework
import json
import os
from dotenv import load_dotenv
from googleapiclient import discovery

load_dotenv()
PROJECT = os.getenv("GCP_PROJECT")
# Comma-separated list of instance:zone pairs, e.g. "vm1:zone1,vm2:zone2"
INSTANCES_ZONES = os.getenv("INSTANCES_ZONES")

# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def le_pubsub(cloud_event):
    # Decode the Pub/Sub message data (expects '1' to start, '0' to stop)
    data = cloud_event.data.get("message", {}).get("data")
    if not data:
        print("No data in Pub/Sub message.")
        return

    payload = base64.b64decode(data).decode("utf-8").strip()
    try:
        action = int(payload)
    except ValueError:
        print(f"Invalid payload '{payload}'. Expected '1' (start) or '0' (stop).")
        return
    # Parse instance-zone pairs from INSTANCES_ZONES env var
    if not INSTANCES_ZONES:
        print("No instance-zone pairs defined. Set INSTANCES_ZONES to 'inst1:zone1,inst2:zone2,...'")
        return
    entries = [e.strip() for e in INSTANCES_ZONES.split(",") if e.strip()]
    instance_zone_pairs = []

    for entry in entries:
        if ":" not in entry:
            print(f"Invalid format '{entry}'. Expected 'instance:zone'.")
            return
        inst, zone = entry.split(":", 1)
        instance_zone_pairs.append((inst, zone))

    start_stop_instances(action, instance_zone_pairs)


def start_stop_instances(action, instance_zone_pairs): 
    compute = discovery.build("compute", "v1")  
    if action == 1:
        for inst, zone in instance_zone_pairs:
            print(f"Starting VM: project={PROJECT}, zone={zone}, instance={inst}")
            op = compute.instances().start(project=PROJECT, zone=zone, instance=inst).execute()
            print(f"Start operation for {inst} in zone {zone} response: {op}")

    elif action == 0:
        for inst, zone in instance_zone_pairs:
            print(f"Stopping VM: project={PROJECT}, zone={zone}, instance={inst}")
            op = compute.instances().stop(project=PROJECT, zone=zone, instance=inst).execute()
            print(f"Stop operation for {inst} in zone {zone} response: {op}")

    else:
        print(f"Unknown action '{action}'. Expected 1 or 0.")
