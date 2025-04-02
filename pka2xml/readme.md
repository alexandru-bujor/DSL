Convert Packet Tracer network simulation pka and pkt files into XML and vice versa.


## Building
### Building manually
To build a static binary:

```
make static-install
```

To build a dynamic binary:
```
make dynamic-install
```

## `pka2xml`
```
usage: pka2xml [ options ]

where options are:
  -d <in> <out>   decrypt pka/pkt to xml
  -e <in> <out>   encrypt pka/pkt to xml

  -f <in> <out>   allow packet tracer file to be read by any version

  -nets <in>      decrypt packet tracer "nets" file
  -logs <in>      decrypt packet tracer log file

  --forge <out>   forge authentication file to bypass login


examples:
  pka2xml -d foobar.pka foobar.xml
  pka2xml -e foobar.xml foobar.pka
  pka2xml -nets $HOME/packettracer/nets
  pka2xml -logs $HOME/packettracer/pt_12.05.2020_21.07.17.338.log
```

## `PacketTracer` (`patch.c`)
Launch PacketTracer with the following patches:
- bypass login screen
- display all activities as completed
- unlock all previously locked interfaces
- don't reset activity on user change

## `graph.py`
Given an xml file of a Packet Tracer Network Simulation, generates a graph of the entire network.

## Dependencies
- CryptoPP
- libzip
- Re2
