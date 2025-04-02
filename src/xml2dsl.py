#!/usr/bin/env python3
import sys
import xml.etree.ElementTree as ET

# Map Packet Tracer model strings to DSL device keywords
MODEL_MAP = {
    "PC-PT": "pc",
    "Laptop-PT": "laptop",
    "2960-24TT": "switch",
    # Add more as needed...
}


def parse_bandwidth_to_mbps(bw_str):
    """Convert Packet Tracer bandwidth strings to integer Mbps."""
    try:
        bw_val = int(bw_str)
        # Packet Tracer often uses 100,000 for FastEthernet (100Mbps),
        # 1,000,000 for GigabitEthernet (1000Mbps), etc.
        return bw_val // 1000
    except:
        return 0


def main(input_xml, output_dsl):
    # Parse the XML
    tree = ET.parse(input_xml)
    root = tree.getroot()

    # Dictionary to hold device data keyed by save-ref-id
    devices = {}
    # List for link data
    links = []

    network_tag = root.find("./NETWORK")
    if network_tag is None:
        print(f"ERROR: No <NETWORK> tag found in {input_xml}")
        return

    devices_tag = network_tag.find("DEVICES")
    if devices_tag is None:
        print(f"ERROR: No <DEVICES> section found in {input_xml}")
        return

    # 1) Collect devices
    for dev_elem in devices_tag.findall("DEVICE"):
        engine_elem = dev_elem.find("ENGINE")
        if engine_elem is None:
            continue

        # Name and Type
        dev_name = engine_elem.findtext("NAME", "Unknown")
        model_attr = engine_elem.find("TYPE").get("model", "") if engine_elem.find("TYPE") is not None else ""
        dsl_type = MODEL_MAP.get(model_attr, "unknown")

        # Coordinates & Power
        x_coord = engine_elem.findtext("./COORD_SETTINGS/X_COORD", "0")
        y_coord = engine_elem.findtext("./COORD_SETTINGS/Y_COORD", "0")
        power_str = engine_elem.findtext("POWER", "false")
        is_power_on = (power_str.lower() == "true")

        # Save-ref-id for cross-referencing in LINK
        save_ref_id = engine_elem.findtext("SAVE_REF_ID", "")

        # Gather PORT info
        ports_info = {}
        for port in dev_elem.findall(".//PORT"):
            bw_str = port.findtext("BANDWIDTH", "100000")
            bw_mbps = parse_bandwidth_to_mbps(bw_str)
            ports_info[id(port)] = {
                "bandwidth_mbps": bw_mbps
            }

        devices[save_ref_id] = {
            "name": dev_name,
            "dsl_type": dsl_type,
            "x_coord": x_coord,
            "y_coord": y_coord,
            "power_on": is_power_on,
            "ports": ports_info,
        }

    # 2) Collect links
    links_tag = network_tag.find("LINKS")
    if links_tag is None:
        print("No <LINKS> found—no links to process.")
    else:
        for link_elem in links_tag.findall("LINK"):
            cable = link_elem.find("CABLE")
            if cable is None:
                continue

            from_ref = cable.findtext("FROM", "")
            to_ref = cable.findtext("TO", "")

            ports = cable.findall("PORT")
            if len(ports) < 2:
                continue  # safety check

            from_port = ports[0].text or ""
            to_port = ports[1].text or ""

            # Simplistic approach for link speed
            if "Gigabit" in from_port:
                link_speed = 1000
            else:
                link_speed = 100

            links.append({
                "from_ref": from_ref,
                "from_port": from_port,
                "to_ref": to_ref,
                "to_port": to_port,
                "speed": link_speed
            })

    # 3) Build DSL output as a string
    lines = []
    lines.append("network MyNetwork {")
    for dev in devices.values():
        lines.append(f"    device {dev['name']} {dev['dsl_type']} {{")
        lines.append(f"        coordinates {dev['x_coord']} {dev['y_coord']}")
        if dev["power_on"]:
            lines.append("        power on")
        # For simplicity, we create a single interface
        # If you want to represent all ports, you’d loop over dev["ports"].
        lines.append("        interface FastEthernet0 {")
        # IP is often missing in PT’s raw XML, so using a placeholder here
        lines.append("            ip 0.0.0.0")
        if dev["ports"]:
            # Use the first port’s bandwidth for demonstration
            first_port_id = next(iter(dev["ports"]))
            bw_val = dev["ports"][first_port_id]["bandwidth_mbps"]
            lines.append(f"            bandwidth {bw_val}")
        lines.append("        }")
        lines.append("    }")

    # Links
    for link in links:
        from_dev = devices.get(link["from_ref"], {}).get("name", "UNKNOWN")
        to_dev = devices.get(link["to_ref"], {}).get("name", "UNKNOWN")
        lines.append(f"    link {from_dev}.{link['from_port']} -> {to_dev}.{link['to_port']} {{")
        lines.append(f"        speed {link['speed']}")
        lines.append("    }")

    lines.append("}")

    dsl_output = "\n".join(lines)

    # 4) Write the DSL output to a .dsl file
    with open(output_dsl, "w", encoding="utf-8") as f:
        f.write(dsl_output + "\n")
    print(f"DSL saved to {output_dsl}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python xml2dsl.py <input-xml> <output.dsl>")
        sys.exit(1)

    input_xml_file = sys.argv[1]
    output_dsl_file = sys.argv[2]
    #input_xml_file = "../convertions/test-file-1.xml"
    #output_dsl_file = "../dsl/output1.dsl"
    main(input_xml_file, output_dsl_file)
