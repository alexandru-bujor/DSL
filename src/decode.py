import sys
import xml.etree.ElementTree as ET
import json
from ipaddress import ip_address

# Map Packet Tracer model strings to DSL device keywords
MODEL_MAP = {
    "PC-PT": "pc",
    "Laptop-PT": "laptop",
    "2960-24TT": "switch",
    "ISR4331": "router",
    "Server-PT": "server",
}

# Map device types to image URLs
IMAGE_MAP = {
    "pc": "/images/pc.png",
    "laptop": "/images/laptop.png",
    "switch": "/images/switch.png",
    "router": "/images/router.png",
    "server": "/images/server.png",
    "unknown": "/images/unknown.png",
}

def parse_bandwidth_to_mbps(bw_str):
    """Convert Packet Tracer bandwidth strings to integer Mbps."""
    try:
        bw_val = int(bw_str)
        return bw_val // 1000
    except:
        return 0

def generate_dsl_and_react_flow(input_xml, output_dsl):
    # Parse the XML
    tree = ET.parse(input_xml)
    root = tree.getroot()

    devices = {}
    links = []
    device_id_counter = 1
    device_map = {}

    network_tag = root.find("./NETWORK")
    if network_tag is None:
        print(f"ERROR: No <NETWORK> tag found in {input_xml}", file=sys.stderr)
        sys.exit(1)

    devices_tag = network_tag.find("DEVICES")
    if devices_tag is None:
        print(f"ERROR: No <DEVICES> section found in {input_xml}", file=sys.stderr)
        sys.exit(1)

    # Collect devices
    for dev_elem in devices_tag.findall("DEVICE"):
        engine_elem = dev_elem.find("ENGINE")
        workspace_elem = dev_elem.find("WORKSPACE")
        if engine_elem is None:
            continue

        dev_name = engine_elem.findtext("NAME", "Unknown")

        if dev_name == "Power Distribution Device0":
            continue

        model_attr = engine_elem.find("TYPE").get("model", "") if engine_elem.find("TYPE") is not None else ""
        dsl_type = MODEL_MAP.get(model_attr, "unknown")
        x_coord = float(workspace_elem.findtext("./LOGICAL/X", "0"))
        y_coord = float(workspace_elem.findtext("./LOGICAL/Y", "0"))
        power_str = engine_elem.findtext("POWER", "false")
        is_power_on = (power_str.lower() == "true")
        save_ref_id = engine_elem.findtext("SAVE_REF_ID", "")

        ports_info = {}
        ip_address = "0.0.0.0"
        for port in dev_elem.findall(".//PORT"):
            bw_str = port.findtext("BANDWIDTH", "100000")
            bw_mbps = parse_bandwidth_to_mbps(bw_str)
            port_ip = port.findtext("IP")

            if port_ip and port_ip.strip():
                ip_address = port_ip

            ports_info[id(port)] = {"bandwidth_mbps": bw_mbps}

        devices[save_ref_id] = {
            "id": device_id_counter,
            "name": dev_name,
            "dsl_type": dsl_type,
            "x_coord": x_coord,
            "y_coord": y_coord,
            "power_on": is_power_on,
            "ports": ports_info,
            "ip_address": ip_address,
        }
        device_map[save_ref_id] = device_id_counter
        device_id_counter += 1

    # Collect links
    links_tag = network_tag.find("LINKS")
    if links_tag:
        for link_elem in links_tag.findall("LINK"):
            cable = link_elem.find("CABLE")
            if cable is None:
                continue

            from_ref = cable.findtext("FROM", "")
            to_ref = cable.findtext("TO", "")
            ports = cable.findall("PORT")
            if len(ports) < 2:
                continue

            from_port = ports[0].text or ""
            to_port = ports[1].text or ""
            link_speed = 1000 if "Gigabit" in from_port else 100

            links.append({
                "from_ref": from_ref,
                "from_port": from_port,
                "to_ref": to_ref,
                "to_port": to_port,
                "speed": link_speed
            })

    # Build DSL output
    lines = []
    lines.append("network MyNetwork {")
    for dev in devices.values():
        lines.append(f"    device {dev['name']} {dev['dsl_type']} {{")
        lines.append(f"        coordinates {dev['x_coord']} {dev['y_coord']}")
        if dev["power_on"]:
            lines.append("        power on")
        lines.append("        interface FastEthernet0 {")
        lines.append(f"            ip {dev['ip_address']}")
        if dev["ports"]:
            first_port_id = next(iter(dev["ports"]))
            bw_val = dev["ports"][first_port_id]["bandwidth_mbps"]
            lines.append(f"            bandwidth {bw_val}")
        lines.append("        }")
        lines.append("    }")

    for link in links:
        from_dev = devices.get(link["from_ref"], {}).get("name", "UNKNOWN")
        to_dev = devices.get(link["to_ref"], {}).get("name", "UNKNOWN")
        lines.append(f"    link {from_dev}.{link['from_port']} -> {to_dev}.{link['to_port']} {{")
        lines.append(f"        speed {link['speed']}")
        lines.append("    }")

    lines.append("}")
    dsl_output = "\n".join(lines)

    # Write DSL to file
    with open(output_dsl, "w", encoding="utf-8") as f:
        f.write(dsl_output + "\n")

    # Build React Flow JSON
    react_flow_nodes = []
    react_flow_edges = []

    for dev in devices.values():
        node = {
            "id": str(dev["id"]),
            "type": "custom",
            "data": {
                "label": dev["name"],
                "src": IMAGE_MAP.get(dev["dsl_type"], IMAGE_MAP["unknown"]),
                # Add all device characteristics for the modal
                "type": dev["dsl_type"],
                "coordinates": f"{dev['x_coord']} {dev['y_coord']}",
                "power_on": dev["power_on"],
                "interface": {
                    "name": "FastEthernet0",
                    "ip": dev['ip_address'],
                    "bandwidth": dev["ports"][next(iter(dev["ports"]))]["bandwidth_mbps"] if dev["ports"] else 0
                }
            },
            "position": {
                "x": dev["x_coord"],
                "y": dev["y_coord"]
            }
        }
        react_flow_nodes.append(node)

    for i, link in enumerate(links):
        from_id = device_map.get(link["from_ref"])
        to_id = device_map.get(link["to_ref"])
        if from_id and to_id:
            edge = {
                "id": f"e{i}",
                "source": str(from_id),
                "target": str(to_id),
                "type": "straight",
                "animated": True
            }
            react_flow_edges.append(edge)

    # Print React Flow JSON to stdout
    print(json.dumps({"nodes": react_flow_nodes, "edges": react_flow_edges}))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python decode.py <input-xml> <output.dsl>")
        sys.exit(1)

    input_xml_file = sys.argv[1]
    output_dsl_file = sys.argv[2]
    generate_dsl_and_react_flow(input_xml_file, output_dsl_file)