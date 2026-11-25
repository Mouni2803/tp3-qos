import sys
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSBridge
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel


class G1Topo(Topo):
    def build(self, bottleneck=False):
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        g1 = self.addHost('g1')

        for name, ip in [
            ('h1', '10.0.4.11/24'),
            ('h2', '10.0.4.12/24'),
            ('h3', '10.0.4.13/24'),
        ]:
            host = self.addHost(name, ip=ip)
            self.addLink(host, s1, bw=100)

        for name, ip in [
            ('srv1', '10.0.5.21/24'),
            ('srv2', '10.0.5.22/24'),
            ('srv3', '10.0.5.23/24'),
        ]:
            host = self.addHost(name, ip=ip)
            self.addLink(host, s2, bw=100)

        self.addLink(g1, s1, intfName1='g1-eth0', bw=100)
        link_bw = 10 if bottleneck else 100
        self.addLink(g1, s2, intfName1='g1-eth1', bw=link_bw)


def run():
    use_bottleneck = '--bottleneck' in sys.argv
    net = Mininet(
        topo=G1Topo(bottleneck=use_bottleneck),
        switch=OVSBridge,
        link=TCLink,
        controller=None
    )

    net.start()
    g1 = net.get('g1')
    g1.cmd('ip addr flush dev g1-eth0')
    g1.cmd('ip addr flush dev g1-eth1')
    g1.cmd('ip addr add 10.0.4.1/24 dev g1-eth0')
    g1.cmd('ip addr add 10.0.5.1/24 dev g1-eth1')
    g1.cmd('sysctl -w net.ipv4.ip_forward=1')

    for host in ('h1', 'h2', 'h3'):
        net.get(host).cmd('ip route replace default via 10.0.4.1')
    for host in ('srv1', 'srv2', 'srv3'):
        net.get(host).cmd('ip route replace default via 10.0.5.1')

    try:
        CLI(net)
    finally:
        net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()
