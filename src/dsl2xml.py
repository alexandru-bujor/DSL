import sys
import xml.etree.ElementTree as ET
from pyparsing import (
    Word, alphanums, alphas, Suppress, Keyword, Group, Optional,
    OneOrMore, Literal, ParseException
)
from pyparsing import pyparsing_common as ppc

# Define grammar
ID = Word(alphanums + "_-/.")

NUMBER = ppc.fnumber
IPADDR = Word(alphanums + "./")

LBRACE, RBRACE = map(Suppress, "{}")

# DSL keywords
network_kw = Keyword("network")
device_kw = Keyword("device")
coordinates_kw = Keyword("coordinates")
power_kw = Keyword("power")
interface_kw = Keyword("interface")
ip_kw = Keyword("ip")
bandwidth_kw = Keyword("bandwidth")
link_kw = Keyword("link")

# Interface block
InterfaceBody = Group(
    interface_kw + ID("iface_name") + LBRACE +
    ip_kw + IPADDR("ip") +
    Optional(bandwidth_kw + NUMBER("bandwidth")) +
    RBRACE
)

# Device block
Device = Group(
    device_kw + ID("name") + ID("type") +
    LBRACE +
    coordinates_kw + NUMBER("x") + NUMBER("y") +
    Optional(power_kw + Keyword("on"))("power") +
    InterfaceBody("interface") +
    RBRACE
)

# Link block
Link = Group(
    link_kw +
    Group(ID("from_dev") + Suppress(".") + ID("from_port"))("from") +
    Suppress("->") +
    Group(ID("to_dev") + Suppress(".") + ID("to_port"))("to") +
    LBRACE +
    Optional(Keyword("speed") + NUMBER("speed")) +
    RBRACE
)

# Network block
Network = Group(
    network_kw + ID("name") +
    LBRACE +
    OneOrMore(Device)("devices") +
    OneOrMore(Link)("links") +
    RBRACE
)

def parse_dsl(text):
    try:
        return Network.parseString(text, parseAll=True)
    except ParseException as e:
        print(f"Parsing error: {e}")
        sys.exit(1)

def build_xml(parsed):
    root = ET.Element("NETWORK")

    devices_el = ET.SubElement(root, "DEVICES")
    save_id_counter = 1000

    save_id_map = {}

    for dev in parsed["devices"]:
        device_el = ET.SubElement(devices_el, "DEVICE")
        engine = ET.SubElement(device_el, "ENGINE")
        workspace = ET.SubElement(device_el, "WORKSPACE")
        logical = ET.SubElement(ET.SubElement(workspace, "LOGICAL"))

        ET.SubElement(engine, "NAME").text = dev["name"]
        ET.SubElement(engine, "TYPE", model=dev["type"])
        ET.SubElement(engine, "POWER").text = "true" if dev.get("power") else "false"
        ET.SubElement(engine, "SAVE_REF_ID").text = str(save_id_counter)

        ET.SubElement(engine, "PORTS")  # Placeholder

        ET.SubElement(logical, "X").text = str(dev["x"])
        ET.SubElement(logical, "Y").text = str(dev["y"])

        iface = dev["interface"]
        port_el = ET.SubElement(device_el, "PORT")
        ET.SubElement(port_el, "IP").text = iface["ip"]
        ET.SubElement(port_el, "BANDWIDTH").text = str(int(iface.get("bandwidth", 100) * 1000))

        save_id_map[dev["name"]] = str(save_id_counter)
        save_id_counter += 1

    links_el = ET.SubElement(root, "LINKS")

    for link in parsed["links"]:
        link_el = ET.SubElement(links_el, "LINK")
        cable = ET.SubElement(link_el, "CABLE")

        from_id = save_id_map.get(link["from"]["from_dev"], "0")
        to_id = save_id_map.get(link["to"]["to_dev"], "0")

        ET.SubElement(cable, "FROM").text = from_id
        ET.SubElement(cable, "PORT").text = link["from"]["from_port"]
        ET.SubElement(cable, "TO").text = to_id
        ET.SubElement(cable, "PORT").text = link["to"]["to_port"]

        speed = int(link.get("speed", 100))
        ET.SubElement(cable, "TYPE").text = "eStraightThrough"
        ET.SubElement(cable, "LENGTH").text = "42.00"
        ET.SubElement(cable, "FUNCTIONAL").text = "true"

    return ET.ElementTree(root)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python dsl2xml.py <input.dsl> <output.xml>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, "r", encoding="utf-8") as f:
        dsl_text = f.read()

    parsed = parse_dsl(dsl_text)
    tree = build_xml(parsed)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    print(f"✅ XML file saved to {output_file}")
