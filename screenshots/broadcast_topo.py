from mininet.net import Mininet
from mininet.node import OVSController, OVSSwitch, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import TCLink

def broadcast_topology():
    net = Mininet(controller=OVSController, switch=OVSSwitch, link=TCLink)

    print("*** Creating controller")
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6633)

    print("*** Creating switch")
    s1 = net.addSwitch('s1')

    print("*** Creating 4 hosts")
    h1 = net.addHost('h1', ip='10.0.0.1/24')
    h2 = net.addHost('h2', ip='10.0.0.2/24')
    h3 = net.addHost('h3', ip='10.0.0.3/24')
    h4 = net.addHost('h4', ip='10.0.0.4/24')

    print("*** Adding links")
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(h3, s1)
    net.addLink(h4, s1)

    print("*** Starting network")
    net.start()

    print("*** Network ready. Entering CLI")
    CLI(net)

    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    broadcast_topology()
