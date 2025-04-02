import xml.etree.ElementTree as ET
import os
import re
import sys
import string

try:
    from ipaddress import ip_network as IPAddress
except ImportError:
    def IPAddress(ip): return ip  # fallback dummy function

# Require filepath as argument
if len(sys.argv) < 2:
    print("Usage: python graph.py <file.xml>")
    exit(1)

filepath = sys.argv[1]

# Read and clean file
with open(filepath, encoding='utf-8', errors='ignore') as f:
    data = f.read()

data = re.sub(f'[^{re.escape(string.printable)}]', '', data)
root = ET.fromstring(data)

# Get value by XML path
def get_value(node, path):
    v = node.find(path)
    return v.text.strip() if v is not None and v.text else ''

class Port:
    def __init__(self, node, index, parent_type, dev_name=''):
        self.type = get_value(node, 'TYPE')
        self.mac = get_value(node, 'MACADDRESS')
        self.ip = get_value(node, 'IP')
        self.sub = get_value(node, 'SUBNET')
        self.dhcp = get_value(node, 'PORT_DHCP_ENABLE')

        if self.dhcp == 'true':
            self.ip = '<DHCP>'

        main_switch = {
            'Pc': 1, 'Pda': 1, 'Cloud': 1, 'Laptop': 1,
            'Printer': 1, 'Server': 1,
            'AccessPoint': 2, 'DslModem': 2, 'Router': 2,
            'Sniffer': 2, 'Switch': 2, 'WirelessRouter': 2,
        }

        switch = {
            1: {
                'eCopperEthernet': 'Ethernet{}',
                'eCopperFastEthernet': 'FastEthernet{}',
                'eCopperGigabitEthernet': 'GigabitEthernet{}',
                'eAccessPointWirelessN': '{}',
                'eCopperCoaxial': '{}',
                'eHostWirelessN': '{}',
                'eModem': '{}',
                'eSerial': '{}',
            },
            2: {
                'eCopperEthernet': 'Ethernet{}',
                'eCopperFastEthernet': 'FastEthernet0/{}',
                'eCopperGigabitEthernet': 'GigabitEthernet0/{}',
                'eAccessPointWirelessN': '{}',
                'eCopperCoaxial': '{}',
                'eHostWirelessN': '{}',
                'eModem': '{}',
                'eSerial': '{}',
            },
        }

        self.name = '<Unnamed>'
        if self.type and parent_type in main_switch:
            fmt = switch[main_switch[parent_type]].get(self.type, '{}')
            self.name = fmt.format(index)

        if dev_name:
            self.name = dev_name

    def __repr__(self):
        return self.name

class Ports:
    def __init__(self, node):
        self.ports = []
        count = {}

        lines = node.findall('ENGINE/RUNNINGCONFIG/LINE')
        names = [j.text.split(' ')[1] for j in lines if j.text and 'interface' in j.text]

        for i, p in enumerate(node.findall('ENGINE/MODULE/SLOT/MODULE/PORT')):
            v = get_value(p, 'TYPE')
            count[v] = count.get(v, -1) + 1
            dev_type = get_value(node, 'ENGINE/TYPE')
            dev_name = names[i] if i < len(names) else ''
            self.ports.append(Port(p, count[v], dev_type, dev_name))

    def by_name(self, name):
        for port in self.ports:
            if port.name == name:
                return port
        return None

class Device:
    def __init__(self, node):
        self.node = node
        self.type = get_value(node, 'ENGINE/TYPE')
        self.name = get_value(node, 'ENGINE/NAME')
        self.id = get_value(node, 'ENGINE/SAVE_REF_ID')
        self.ports = Ports(node)

class Devices:
    def __init__(self, nodes):
        self.devices = [Device(d) for d in nodes.findall('PACKETTRACER5/NETWORK/DEVICES/DEVICE')]
        if not self.devices:
            self.devices = [Device(d) for d in nodes.findall('NETWORK/DEVICES/DEVICE')]

    def by_id(self, id):
        for device in self.devices:
            if device.id == id:
                return device
        return None

    def by_index(self, index):
        try:
            return self.devices[int(index)]
        except (ValueError, IndexError):
            return None

devices = Devices(root)

def traverse(nodes, fn, depth=0):
    for node in nodes:
        fn(node, depth)
        children = node.findall('NODE')
        if children:
            traverse(children, fn, depth + 1)

def printer(node, depth):
    name = node.find('NAME')
    if name is not None and name.attrib.get('checkType') in ('1', '2'):
        print('  ' * depth + name.text, name.attrib.get('nodeValue'))

traverse(root.findall('COMPARISONS/NODE'), printer)
traverse(root.findall('INITIALSETUP/NODE'), printer)

# Try both XML structures
links = root.find('PACKETTRACER5/NETWORK/LINKS') or root.find('NETWORK/LINKS')
if links is None:
    print("[ERROR] No LINKS section found in XML.")
    exit(1)

with open('network.dot', 'w') as f:
    f.write('graph G {\n')
    f.write('\tnode [style=rounded,shape=record];\n')
    f.write('\tlayout=twopi;\n')
    f.write('\tgraph [pad="1", ranksep="1.5"];\n\n')

    for link in links:
        from_id = link.findtext('CABLE/FROM')
        to_id = link.findtext('CABLE/TO')

        fr = devices.by_index(from_id) or devices.by_id(from_id)
        to = devices.by_index(to_id) or devices.by_id(to_id)

        if not fr or not to:
            print(f"[WARNING] Could not find device(s) FROM='{from_id}' TO='{to_id}'")
            continue

        ports = link.findall('CABLE/PORT')
        if len(ports) < 2:
            print("[WARNING] Link missing ports.")
            continue

        fr_port = fr.ports.by_name(ports[0].text)
        to_port = to.ports.by_name(ports[1].text)

        if not fr_port or not to_port:
            print(f"[WARNING] Could not find ports: {ports[0].text}, {ports[1].text}")
            continue

        fr_ip, fr_sub = fr_port.ip, fr_port.sub
        to_ip, to_sub = to_port.ip, to_port.sub

        try:
            fr_sub = IPAddress(f"{fr_ip}/{fr_sub}").prefixlen
        except: pass
        try:
            to_sub = IPAddress(f"{to_ip}/{to_sub}").prefixlen
        except: pass

        f.write('\t"{}"--"{}" [taillabel="{}{}{}"; headlabel="{}{}{}"];\n'.format(
            fr.name, to.name,
            fr_ip, '/' if fr_sub else '', fr_sub,
            to_ip, '/' if to_sub else '', to_sub))

    f.write('}\n')

# Generate image using Graphviz
os.system('dot -Tpng network.dot -o network.png')
print("✅ network.png generated successfully.")
