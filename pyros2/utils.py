import netifaces as nt

from icecream import ic

def ip4_addresses():
    ip_list = []
    for interface in nt.interfaces():
        net = nt.ifaddresses(interface)
        if nt.AF_INET in net:
            links = net[nt.AF_INET]
            for link in links:
                ip_list.append(link["addr"])
    return ip_list

if __name__=="__main__":
    # interface = nt.interfaces()
    # ic(interface)
    # for interface in nt.interfaces():
    #     ic(interface)
    #     net = nt.ifaddresses(interface)
    #     # ic(net)

    #     if nt.AF_INET in net:
    #         links = net[nt.AF_INET]
    #         for link in links:
    #             ic(link["addr"])


    ips = ip4_addresses()
    print(ips)