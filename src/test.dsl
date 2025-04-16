network MyNetwork {
    device PC0 pc {
        coordinates 168.5 288.0
        power on
        interface FastEthernet0 {
            ip 192.168.1.10
            bandwidth 100
        }
    }
    device PC99 pc {
        coordinates 178.5 278.0
        power on
        interface FastEthernet0 {
            ip 192.168.1.9
            bandwidth 100
        }
    }
    device Laptop0 laptop {
        coordinates 284.5 365.0
        power on
        interface FastEthernet0 {
            ip 192.168.1.12
            bandwidth 100
        }
    }
    device Server0 server {
        coordinates 175.0 166.0
        power on
        interface FastEthernet0 {
            ip 192.168.1.11
            bandwidth 100
        }
    }
    device Switch0 switch {
        coordinates 343.0 227.0
        power on
        interface FastEthernet0 {
            ip 0.0.0.0
            bandwidth 100
        }
    }
    device Switch1 switch {
        coordinates 536.0 227.0
        power on
        interface FastEthernet0 {
            ip 0.0.0.0
            bandwidth 100
        }
    }
    device PC1 pc {
        coordinates 638.5 363.0
        power on
        interface FastEthernet0 {
            ip 192.168.2.12
            bandwidth 100
        }
    }
    device Laptop1 laptop {
        coordinates 739.5 169.0
        power on
        interface FastEthernet0 {
            ip 192.168.2.10
            bandwidth 100
        }
    }
    device Server1 server {
        coordinates 724.0 287.0
        power on
        interface FastEthernet0 {
            ip 192.168.2.11
            bandwidth 100
        }
    }
    device Router0 router {
        coordinates 449.5 314.0
        power on
        interface FastEthernet0 {
            ip 0.0.0.0
            bandwidth 1000
        }
    }
    link Server0.FastEthernet0 -> Switch0.FastEthernet0/1 {
        speed 100
    }
    link PC0.FastEthernet0 -> Switch0.FastEthernet0/2 {
        speed 100
    }
    link Laptop0.FastEthernet0 -> Switch0.FastEthernet0/3 {
        speed 100
    }
    link Switch0.GigabitEthernet0/1 -> Router0.GigabitEthernet0/0/0 {
        speed 1000
    }
    link PC1.FastEthernet0 -> Switch1.FastEthernet0/1 {
        speed 100
    }
    link Server1.FastEthernet0 -> Switch1.FastEthernet0/2 {
        speed 100
    }
    link Laptop1.FastEthernet0 -> Switch1.FastEthernet0/3 {
        speed 100
    }
    link Switch1.GigabitEthernet0/1 -> Router0.GigabitEthernet0/0/1 {
        speed 1000
    }
    link Switch0.FastEthernet0/4 -> Switch1.FastEthernet0/4 {
        speed 100
    }
}