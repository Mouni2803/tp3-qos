from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSBridge
from mininet.link import TCLink
class QoSTopo(Topo):
    def build(self):
        s1 = self.addSwitch('s1')
        for name in ('h1', 'h2', 'h3', 'srv1', 'srv2', 'srv3'):
            host= self.addHost(name)
            self.addLink(host,s1)
def run():
    net= Mininet(topo=QoSTopo(), switch=OVSBridge, link=TCLink, controller=None)
    net.start()
    net.pingAll()
    net.stop()

if __name__=='__main__':
   run()


