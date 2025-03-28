from pyparsing import Group, ZeroOrMore
from lex import W, IPV4_ADDRESS, NUMBER, LBRACE, RBRACE, Keyword, Literal, Suppress

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
