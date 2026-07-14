import json, subprocess, sys

# Get network info
r = subprocess.run(["docker", "network", "inspect", "pkb_pkb-net"], capture_output=True, text=True)
data = json.loads(r.stdout)

print("=== Containers on pkb_pkb-net ===")
for cid, c in data[0].get("Containers", {}).items():
    print(f'  {c["Name"]:30s}  {c.get("IPv4Address", "N/A"):20s}  EndpointID={cid[:12]}')

# Get docling container info
r2 = subprocess.run(["docker", "inspect", "docling-serve-cpu"], capture_output=True, text=True)
doc = json.loads(r2.stdout)
networks = doc[0]["NetworkSettings"]["Networks"]
print("\n=== docling-serve-cpu network(s) ===")
for net_name, net_data in networks.items():
    print(f'  {net_name}: IP={net_data.get("IPAddress","?")} EndpointID={net_data.get("EndpointID","?")[:12]}')

r3 = subprocess.run(["docker", "inspect", "pkb-parser"], capture_output=True, text=True)
par = json.loads(r3.stdout)
networks2 = par[0]["NetworkSettings"]["Networks"]
print("\n=== pkb-parser network(s) ===")
for net_name, net_data in networks2.items():
    print(f'  {net_name}: IP={net_data.get("IPAddress","?")} EndpointID={net_data.get("EndpointID","?")[:12]}')
