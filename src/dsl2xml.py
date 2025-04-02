import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom
from src.parser import Network
from pyparsing import ParseResults

def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, encoding="unicode")
    return minidom.parseString(rough_string).toprettyxml(indent="  ")

def inject_into_template(parsed_result):
    """Inject parsed DSL data into an XML template."""
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

    network_data = parsed_result[0] if len(parsed_result) == 1 else parsed_result

    for item in network_data[2:]:
        if not isinstance(item, ParseResults) or not item:
            continue

        token = item[0]
        if token == "device":
            dev_elem = ET.SubElement(devices_elem, "DEVICE")
            dev_elem.set("name", item[1])
            dev_elem.set("type", item[2])
            for prop in item[3:]:
                if prop[0] == "coordinates":
                    coord_elem = ET.SubElement(dev_elem, "COORDINATES")
                    coord_elem.set("x", prop[1])
                    coord_elem.set("y", prop[2])
                elif prop[0] == "power":
                    dev_elem.set("power", prop[1])
                elif prop[0] == "interface":
                    iface_elem = ET.SubElement(dev_elem, "INTERFACE")
                    iface_elem.set("name", prop[1])
                    for sub in prop[2:]:
                        if sub[0] == "bandwidth":
                            iface_elem.set("bandwidth", sub[1])
                        elif sub[0] == "ip":
                            iface_elem.set("ip", sub[1])
        elif token == "link":
            link_elem = ET.SubElement(links_elem, "LINK")
            link_details = item[1]
            if len(link_details) >= 7:
                link_elem.set("from", link_details[0])
                link_elem.set("from_port", link_details[2])
                link_elem.set("to", link_details[4])
                link_elem.set("to_port", link_details[6])
            for prop in item[2:]:
                link_elem.set(prop[0], prop[1])

    return prettify_xml(root)

def process_dsl_to_xml(input_file, output_file):
    """Processes a DSL file and generates an XML file."""
    with open(input_file, "r") as f:
        dsl_data = f.read()

    if not dsl_data.strip():
        raise ValueError("DSL file is empty.")

    parsed_result = Network.parseString(dsl_data, parseAll=True)
    xml_output = inject_into_template(parsed_result)

    with open(output_file, "w") as f:
        f.write(xml_output)

    return output_file
def main():
    """Main function to handle DSL processing."""
    # input_file = "../dsl/network.dsl"
    input_file = "../dsl/network.dsl"
    output_file = "../xml/output/final_output.xml"

    print("[INFO] Starting DSL to XML conversion...")

    try:
        process_dsl_to_xml(input_file, output_file)
        print(f"[INFO] Successfully generated XML: {output_file}")
    except Exception as e:
        print(f"[ERROR] Failed to process DSL file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
