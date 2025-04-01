network MyNetwork {
    device PC1 pc {
        coordinates 100 200
        power on
        interface eth0 {
            ip 192.168.1.2
            bandwidth 1000
        }
    }
    device PC2 pc {
        coordinates 100 300
        power on
        interface eth0 {
            ip 192.168.1.3
            bandwidth 1000
        }
    }
    device SW1 switch {
        coordinates 150 250
        interface port1 {
            bandwidth 1000
        }
    }
    link PC1.eth0 -> SW1.port1 {
        speed 100
    }
    link PC1.eth0 -> SW1.port2 {
        speed 100
    }
}