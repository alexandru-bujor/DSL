from pyparsing import Word, alphas, alphanums, Literal, Regex, Keyword, Group, ZeroOrMore, nums

# Lexical patterns

# ID: alphanumeric identifiers, with underscores and hyphens allowed
ID = Word(alphas + "_", alphanums + "_-")

# Numbers and strings
NUMBER = Word(nums)  # Use nums to match digits
STRING = Word(alphas + " ", alphanums + " _")
IPV4_ADDRESS = Regex(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
MAC_ADDRESS = Regex(r"[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}")

# Keywords (network constructs)
NETWORK = Keyword("network")
DEVICE = Keyword("device")
MODULE = Keyword("module")
SLOT = Keyword("slot")
INTERFACE = Keyword("interface")
VLAN = Keyword("vlan")
ROUTE = Keyword("route")
DHCP = Keyword("dhcp")
ACL = Keyword("acl")
LINK = Keyword("link")
COORDINATES = Keyword("coordinates")
POWER = Keyword("power")
GATEWAY = Keyword("gateway")
DNS = Keyword("dns")
BANDWIDTH = Keyword("bandwidth")
VLAN_MODE = Keyword("vlan")
ALLOW = Keyword("allow")
DENY = Keyword("deny")
FROM = Keyword("from")
TO = Keyword("to")
POOL = Keyword("pool")
NAME = Keyword("name")
DESC = Keyword("desc")
CABLE = Keyword("cable")
LENGTH = Keyword("length")
FUNCTIONAL = Keyword("functional")
STATIC = Keyword("static")


# Indentation rule for blocks
def IndentedBlock(expr):
    return ZeroOrMore(Group(expr))
