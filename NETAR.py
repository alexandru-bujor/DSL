from parse import parse_network_definition, NetworkDefinition

network_config = """
network MyNetwork
    device PC1 pc
        coordinates 50 100
        power on
        interface FastEthernet0
            bandwidth 100
            ip 192.168.1.1/24
    link PC1.FastEthernet0 -> Router.GigabitEthernet0
        cable straightThrough
    vlan 10
        name "Office Network"
        desc "Main office VLAN"
    route static
        destination 192.168.1.0/24
        next-hop 192.168.1.1
    acl BlockPing
        allow icmp from 192.168.1.0/24 to any
        deny icmp from any to 192.168.1.0/24
"""


parsed_result = parse_network_definition(network_config)
print(parsed_result)
