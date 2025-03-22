from pyparsing import Keyword, Word, Group, ZeroOrMore, Literal, Optional, Regex, alphas, nums

# Define words and symbols
W = Word(alphas + nums + "-")  # Words with letters, digits, and hyphens
IPV4_ADDRESS = Regex(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')  # Simple IPv4 regex
NUMBER = Word(nums)  # Matches a number

# Grammar definitions
NetworkName = W
DeviceName = W
DeviceType = Keyword("pc") | Keyword("laptop") | Keyword("router") | Keyword("switch") | Keyword("firewall") | W

# Coordinates, Power and other basic properties
Coordinates = Keyword("coordinates") + NUMBER + NUMBER
PowerSetting = Keyword("power") + (Literal("on") | Literal("off"))

# DHCP definitions
DHCPDefinition = Keyword("dhcp") + Group("pool" + W + Group("network" + IPV4_ADDRESS + IPV4_ADDRESS) | "default-gateway" + IPV4_ADDRESS | "dns" + IPV4_ADDRESS)

# Route definitions
RouteDefinition = Keyword("route") + (Keyword("static") | W) + Group("destination" + IPV4_ADDRESS + "/" + NUMBER)

# ACL definitions
ACLDefinition = Keyword("acl") + W + Group(ZeroOrMore(Keyword("allow") | Keyword("deny") + W + Keyword("from") + IPV4_ADDRESS + "/" + NUMBER + Keyword("to") + IPV4_ADDRESS + "/" + NUMBER))

# Device body, such as interfaces and slots
InterfaceDefinition = Keyword("interface") + W + Group(ZeroOrMore(Keyword("bandwidth") + NUMBER | IPV4_ADDRESS))

# Network Body (Top-level constructs)
DeviceBody = ZeroOrMore(Group(Coordinates | PowerSetting | InterfaceDefinition))

NetworkBody = ZeroOrMore(Group(Keyword("device") + DeviceName + DeviceType + Group(DeviceBody)) |
                         Group(Keyword("link") + Group(DeviceName + "." + W + "->" + DeviceName + "." + W)) |
                         Group(Keyword("vlan") + NUMBER + Group(ZeroOrMore(Group("name" + W | "desc" + W)))) |
                         Group(RouteDefinition) |
                         Group(ACLDefinition) |
                         Group(DHCPDefinition))

# Complete Grammar
NetworkDefinition = Keyword("network") + NetworkName + Group(NetworkBody)

# Parser function with debugging
def parse_network_definition(text):
    try:
        # Enable debugging to see how parsing progresses
        result = NetworkDefinition.setDebug().parseString(text)
        print("Parsed Output:", result.asList())
        return result.asDict()
    except Exception as e:
        # Handle any exceptions with debugging info
        print("Error during parsing:", str(e))

# Test with a sample input string
network_config = """
network myNetwork {
    device router1 pc {
        coordinates 10 20
        power off
        interface eth0 {
            bandwidth 100
            ip 192.168.1.1
        }
    }
    link router1.eth0->router2.eth0 {
        cable straightThrough
    }
}
"""

# Call the parser
parsed_result = parse_network_definition(network_config)
if parsed_result:
    print("Successfully parsed the configuration.")
else:
    print("Parsing failed.")
