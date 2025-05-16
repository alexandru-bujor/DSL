import sys
import json
import re

# (Optional) Map DSL type to image path
IMAGE_MAP = {
    "pc": "/images/pc.png",
    "laptop": "/images/laptop.png",
    "switch": "/images/switch.png",
    "router": "/images/router.png",
    "server": "/images/server.png",
    "unknown": "/images/unknown.png",
}

def parse_dsl_to_react_flow(dsl_text):
    nodes = []
    edges = []
    device_map = {}

    dev_pattern = re.compile(r'device\s+(\S+)\s+(\S+)\s*{')
    coord_pattern = re.compile(r'coordinates\s+([\d.]+)\s+([\d.]+)')
    power_pattern = re.compile(r'power\s+on')
    iface_ip_pattern = re.compile(r'ip\s+([\d.]+)')
    iface_bw_pattern = re.compile(r'bandwidth\s+(\d+)')
    link_pattern = re.compile(r'link\s+(\S+)\.(\S+)\s*->\s*(\S+)\.(\S+)\s*{')
    speed_pattern = re.compile(r'speed\s+(\d+)')

    current_device = None
    current_data = {}
    device_id = 1

    lines = dsl_text.splitlines()
    for i, line in enumerate(lines):
        line = line.strip()
        dev_match = dev_pattern.match(line)
        if dev_match:
            current_device = dev_match.group(1)
            dev_type = dev_match.group(2)
            current_data = {
                "id": str(device_id),
                "type": "custom",
                "data": {
                    "label": current_device,
                    "src": IMAGE_MAP.get(dev_type, IMAGE_MAP["unknown"]),
                    "type": dev_type
                },
                "position": { "x": 0, "y": 0 }
            }
            device_map[current_device] = str(device_id)
            device_id += 1
            continue

        coord_match = coord_pattern.match(line)
        if coord_match:
            x, y = float(coord_match.group(1)), float(coord_match.group(2))
            current_data["position"]["x"] = x
            current_data["position"]["y"] = y
            current_data["data"]["coordinates"] = f"{x} {y}"
            continue

        if power_pattern.match(line):
            current_data["data"]["power_on"] = True
            continue

        ip_match = iface_ip_pattern.match(line)
        if ip_match:
            current_data.setdefault("data", {}).setdefault("interface", {})["ip"] = ip_match.group(1)
            continue

        bw_match = iface_bw_pattern.match(line)
        if bw_match:
            current_data["data"].setdefault("interface", {})["bandwidth"] = int(bw_match.group(1))
            continue

        if line == "}":
            if current_device:
                nodes.append(current_data)
                current_device = None
                current_data = {}
            continue

        link_match = link_pattern.match(line)
        if link_match:
            from_dev, from_port, to_dev, to_port = link_match.groups()
            edge_id = f"e{len(edges)}"
            edge = {
                "id": edge_id,
                "source": device_map.get(from_dev, from_dev),
                "target": device_map.get(to_dev, to_dev),
                "type": "straight",
                "animated": True
            }
            edges.append(edge)
            continue

    return { "nodes": nodes, "edges": edges }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python compile.py <input.dsl>", file=sys.stderr)
        sys.exit(1)

    dsl_file = sys.argv[1]
    with open(dsl_file, "r", encoding="utf-8") as f:
        dsl_content = f.read()

    react_json = parse_dsl_to_react_flow(dsl_content)
    print(json.dumps(react_json, indent=2))
