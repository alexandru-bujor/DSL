import sys, json
from pyparsing import Word, alphanums, Suppress, Keyword, Group, Optional, OneOrMore, ParseException
from pyparsing import pyparsing_common as ppc

# Map device types to image URLs
IMAGE_MAP = {
    "pc":     "/images/pc.png",
    "laptop": "/images/laptop.png",
    "switch": "/images/switch.png",
    "router": "/images/router.png",
    "server": "/images/server.png",
    "unknown":"/images/unknown.png",
}

# Lexemes
NAME   = Word(alphanums + "_-" )   # device names
PORT   = Word(alphanums + "_-/")   # port names include slash
NUMBER = ppc.fnumber
IPADDR = Word(alphanums + "./")    # IP addresses
LBRACE, RBRACE = map(Suppress, "{}")

# Keywords
network_kw     = Keyword("network")
device_kw      = Keyword("device")
coordinates_kw = Keyword("coordinates")
power_kw       = Keyword("power")
interface_kw   = Keyword("interface")
ip_kw          = Keyword("ip")
bandwidth_kw   = Keyword("bandwidth")
link_kw        = Keyword("link")

# Grammar
InterfaceBody = Group(
    interface_kw + NAME("iface_name") + LBRACE +
    ip_kw + IPADDR("ip") +
    Optional(bandwidth_kw + NUMBER("bandwidth")) +
    RBRACE
)

Device = Group(
    device_kw + NAME("name") + NAME("type") + LBRACE +
    coordinates_kw + NUMBER("x") + NUMBER("y") +
    Optional(power_kw + Keyword("on"))("power") +
    InterfaceBody("interface") +
    RBRACE
)

Link = Group(
    link_kw +
    Group(NAME("from_dev") + Suppress(".") + PORT("from_port"))("from") +
    Suppress("->") +
    Group(NAME("to_dev")   + Suppress(".") + PORT("to_port"))("to") +
    LBRACE + Optional(Keyword("speed") + NUMBER("speed")) + RBRACE
)

Network = Group(
    network_kw + NAME("name") + LBRACE +
    OneOrMore(Device)("devices") +
    OneOrMore(Link)("links") +
    RBRACE
)


def parse_dsl(text: str):
    try:
        res = Network.parseString(text, parseAll=True)
        return res[0]
    except ParseException as e:
        print(f"DSL parse error: {e}", file=sys.stderr)
        sys.exit(1)


def to_reactflow(parsed):
    devices = parsed.devices
    links   = parsed.links
    name2id = {}
    nodes, edges = [], []

    for idx, dev in enumerate(devices, start=1):
        name2id[dev.name] = str(idx)
        x, y = float(dev.x), float(dev.y)
        iface = dev.interface
        bw    = float(iface.bandwidth) if iface.get("bandwidth") else 0
        nodes.append({
            "id": str(idx),
            "type": "custom",
            "data": {
                "label":       dev.name,
                "src":         IMAGE_MAP.get(dev.type, IMAGE_MAP["unknown"]),
                "type":        dev.type,
                "coordinates": f"{x} {y}",
                "power_on":    bool(dev.power),
                "interface": {
                    "name":      iface.iface_name,
                    "ip":        iface.ip,
                    "bandwidth": bw
                }
            },
            "position": {"x": x, "y": y}
        })

    for i, link in enumerate(links):
        fr = link["from"]["from_dev"]
        to = link["to"]["to_dev"]
        if fr in name2id and to in name2id:
            edges.append({
                "id":       f"e{i}",
                "source":   name2id[fr],
                "target":   name2id[to],
                "type":     "straight",
                "animated": True
            })

    return {"nodes": nodes, "edges": edges}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python dsl2reactflow.py <input.dsl>", file=sys.stderr)
        sys.exit(1)

    text   = open(sys.argv[1], encoding="utf-8").read()
    parsed = parse_dsl(text)
    print(json.dumps(to_reactflow(parsed)))