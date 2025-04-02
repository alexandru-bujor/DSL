network MyNetwork {
    device PC0 pc {
        coordinates 1224.51 1232
        power on
        interface eth0 {
            ip 0.0.0.0
            bandwidth 100
        }
    }
    device Laptop0 laptop {
        coordinates 1229.5 1232
        power on
        interface eth0 {
            ip 0.0.0.0
            bandwidth 100
        }
    }
    device PC1 pc {
        coordinates 1234.49 1232
        power on
        interface eth0 {
            ip 0.0.0.0
            bandwidth 100
        }
    }
    device Switch0 switch {
        coordinates 1269.51 1236.93
        power on
        interface eth0 {
            ip 0.0.0.0
            bandwidth 100
        }
    }
    device Power Distribution Device0 unknown {
        coordinates 1269.51 1236.93
        power on
        interface eth0 {
            ip 0.0.0.0
        }
    }
    link PC0.FastEthernet0 -> Switch0.FastEthernet0 {
        speed 100
    }
    link PC1.FastEthernet0 -> Switch0.FastEthernet0 {
        speed 100
    }
    link Laptop0.FastEthernet0 -> Switch0.FastEthernet0 {
        speed 100
    }
}
