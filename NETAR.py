import xml.etree.ElementTree as ET
from xml.dom import minidom
from pyparsing import (
    Word, alphanums, nums, Literal, Suppress, Regex, Keyword,
    Group, ZeroOrMore, ParseResults
)

# ------------------ DSL PARSER ------------------ #

# Basic tokens
W = Word(alphanums + "-")
IPV4_ADDRESS = Regex(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
NUMBER = Word(nums)
LBRACE, RBRACE = map(Suppress, "{}")

# DSL token definitions
Coordinates = Group(Keyword("coordinates") + NUMBER("x") + NUMBER("y"))
Power = Group(Keyword("power") + (Keyword("on") | Keyword("off"))("state"))
Interface = Group(
    Keyword("interface") + W("name") +
    LBRACE +
    ZeroOrMore(
        Group(Keyword("bandwidth") + NUMBER("bw"))
        | Group(Keyword("ip") + IPV4_ADDRESS("ip"))
    ) +
    RBRACE
)
DeviceBody = ZeroOrMore(Coordinates | Power | Interface)
Device = Group(
    Keyword("device") + W("name") +
    (Keyword("pc") | Keyword("laptop") | Keyword("router") |
     Keyword("switch") | Keyword("firewall") | W)("type") +
    LBRACE +
    DeviceBody +
    RBRACE
)
Link = Group(
    Keyword("link") +
    Group(
        W("device1") + Literal(".") + W("iface1") +
        Literal("->") +
        W("device2") + Literal(".") + W("iface2")
    )("link") +
    LBRACE +
    ZeroOrMore(
        Group(W("property") + W("value"))
    ) +
    RBRACE
)
Network = Group(
    Keyword("network") + W("name") +
    LBRACE +
    ZeroOrMore(Device | Link) +
    RBRACE
)


# ------------------ XML GENERATOR ------------------ #

def prettify_xml(elem):
    """
    Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, encoding="unicode")
    try:
        pretty_xml = minidom.parseString(rough_string).toprettyxml(indent="  ")
    except Exception as e:
        print("Error prettifying XML:", e)
        raise
    return pretty_xml


def inject_into_template(parsed_result):
    """
    Inject the parsed DSL info into an XML template.

    The base XML template is:

    <?xml version="1.0" ?>
    <PACKETTRACER5>
      <VERSION>8.2.2.0400</VERSION>
      <PIXMAPBANK>
        <IMAGE/>
      </PIXMAPBANK>
      <MOVIEBANK/>
      <NETWORK>
        <DEVICES/>
        <LINKS/>
        <SHAPETESTS/>
        <DESCRIPTION/>
      </NETWORK>
      <SCENARIOSET/>
      <OPTIONS/>
    </PACKETTRACER5>
    """
    try:
        # Create the base XML structure.
        root = ET.Element("PACKETTRACER5")
        ET.SubElement(root, "VERSION").text = "8.2.2.0400"
        pixmapbank = ET.SubElement(root, "PIXMAPBANK")
        ET.SubElement(pixmapbank, "IMAGE")
        ET.SubElement(root, "MOVIEBANK")
        network_elem = ET.SubElement(root, "NETWORK")
        devices_elem = ET.SubElement(network_elem, "DEVICES")
        links_elem = ET.SubElement(network_elem, "LINKS")
        ET.SubElement(network_elem, "SHAPETESTS")
        ET.SubElement(network_elem, "DESCRIPTION")
        ET.SubElement(root, "SCENARIOSET")
        ET.SubElement(root, "OPTIONS")
    except Exception as e:
        print("Error while creating the base XML structure:", e)
        raise

    try:
        # The parsed_result from the DSL returns a ParseResults that is a list of one "network" element.
        # To access the network children, flatten it if needed.
        if len(parsed_result) == 1:
            network_data = parsed_result[0]
        else:
            network_data = parsed_result

        # network_data should have the structure:
        # ["network", <network_name>, <child1>, <child2>, ... ]
        print("[DEBUG] Iterating over network children to inject into XML...")
        for item in network_data[2:]:
            if not isinstance(item, ParseResults) or not item:
                continue

            token = item[0]
            if token == "device":
                print(f"[DEBUG] Processing device: {item[1]}")  # device name
                dev_elem = ET.SubElement(devices_elem, "DEVICE")
                dev_elem.set("name", item[1])
                dev_elem.set("type", item[2])
                for prop in item[3:]:
                    if prop[0] == "coordinates":
                        coord_elem = ET.SubElement(dev_elem, "COORDINATES")
                        coord_elem.set("x", prop[1])
                        coord_elem.set("y", prop[2])
                        print(f"  - Added coordinates: x={prop[1]}, y={prop[2]}")
                    elif prop[0] == "power":
                        dev_elem.set("power", prop[1])
                        print(f"  - Added power: {prop[1]}")
                    elif prop[0] == "interface":
                        iface_elem = ET.SubElement(dev_elem, "INTERFACE")
                        iface_elem.set("name", prop[1])
                        for sub in prop[2:]:
                            if sub[0] == "bandwidth":
                                iface_elem.set("bandwidth", sub[1])
                                print(f"    - Added bandwidth: {sub[1]}")
                            elif sub[0] == "ip":
                                iface_elem.set("ip", sub[1])
                                print(f"    - Added IP: {sub[1]}")
            elif token == "link":
                print(
                    f"[DEBUG] Processing link from: {item[1][0]} interface {item[1][2]} to: {item[1][4]} interface {item[1][6]}")
                link_elem = ET.SubElement(links_elem, "LINK")
                # Expected order: [ device1, ".", iface1, "->", device2, ".", iface2 ]
                link_details = item[1]
                if len(link_details) >= 7:
                    link_elem.set("from", link_details[0])
                    link_elem.set("from_port", link_details[2])
                    link_elem.set("to", link_details[4])
                    link_elem.set("to_port", link_details[6])
                else:
                    print("Warning: Unexpected link details format:", link_details)
                for prop in item[2:]:
                    link_elem.set(prop[0], prop[1])
                    print(f"  - Added link property: {prop[0]} = {prop[1]}")
    except Exception as e:
        print("Error injecting DSL info into XML:", e)
        raise

    return prettify_xml(root)


# ------------------ MAIN PIPELINE ------------------ #

def main():
    # ----- Step 1: Load DSL Input -----
    try:
        print("[DEBUG] Loading DSL input from 'network.dsl'...")
        with open("network.dsl", "r") as f:
            dsl_data = f.read()
        if not dsl_data.strip():
            print("Error: The DSL file 'network.dsl' is empty.")
            return
        print("[DEBUG] DSL file read successfully.")
        print("[DEBUG] DSL file content:")
        print(dsl_data)
    except Exception as e:
        print("Error reading DSL file:", e)
        return

    # ----- Step 2: Parse DSL Data -----
    try:
        print("\n[DEBUG] Parsing DSL data...")
        parsed_result = Network.parseString(dsl_data, parseAll=True)
        print("[DEBUG] Parsing successful. Dumped parse structure:")
        print(parsed_result.dump())
    except Exception as e:
        print("Error parsing DSL data:", e)
        return

    # ----- Step 3: Inject DSL Data into XML Template -----
    try:
        print("\n[DEBUG] Injecting parsed DSL data into the XML template...")
        xml_output = inject_into_template(parsed_result)
        print("[DEBUG] XML generated successfully. Printing XML line by line:")
        xml_lines = xml_output.splitlines()
        for line in xml_lines:
            print(line)
    except Exception as e:
        print("Error during XML injection:", e)
        return

    # ----- Step 4: Write XML Output to File -----
    try:
        print("\n[DEBUG] Writing XML output to 'final_output.xml'...")
        with open("final_output.xml", "w") as f:
            f.write(xml_output)
        print("[DEBUG] XML output successfully written to 'final_output.xml'.")
    except Exception as e:
        print("Error writing XML file:", e)
        return


if __name__ == "__main__":
    main()