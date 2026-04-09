from pox.core import core
from pox.lib.util import dpidToStr
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import EthAddr

log = core.getLogger()
BROADCAST_LIMIT = 10
broadcast_count = {}
mac_to_port = {}

class BroadcastController(object):
    def __init__(self, connection):
        self.connection = connection
        connection.addListeners(self)
        log.info("Switch %s connected" % dpidToStr(connection.dpid))
        self.install_broadcast_limit()

    def install_broadcast_limit(self):
        msg = of.ofp_flow_mod()
        msg.match.dl_dst = EthAddr("ff:ff:ff:ff:ff:ff")
        msg.priority = 100
        msg.hard_timeout = 0
        msg.idle_timeout = 0
        msg.actions.append(of.ofp_action_output(port=of.OFPP_CONTROLLER))
        self.connection.send(msg)
        log.info("Broadcast limiting rule installed")

    def _handle_PacketIn(self, event):
        packet = event.parsed
        if not packet.parsed:
            return

        src = str(packet.src)
        dst = str(packet.dst)
        dpid = event.connection.dpid
        in_port = event.port

        if dpid not in mac_to_port:
            mac_to_port[dpid] = {}
        mac_to_port[dpid][src] = in_port

        log.info("Packet in: src=%s dst=%s port=%s" % (src, dst, in_port))

        if dst == "ff:ff:ff:ff:ff:ff":
            broadcast_count[src] = broadcast_count.get(src, 0) + 1
            if broadcast_count[src] > BROADCAST_LIMIT:
                log.warning("BLOCKING broadcast from %s (count=%d)" % (src, broadcast_count[src]))
                msg = of.ofp_flow_mod()
                msg.match.dl_src = EthAddr(src)
                msg.match.dl_dst = EthAddr("ff:ff:ff:ff:ff:ff")
                msg.priority = 200
                msg.hard_timeout = 0
                msg.idle_timeout = 0
                msg.actions = []
                self.connection.send(msg)
                return
            else:
                log.info("ALLOWING broadcast from %s (count=%d)" % (src, broadcast_count[src]))
                msg = of.ofp_packet_out()
                msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
                msg.data = event.ofp
                msg.in_port = in_port
                self.connection.send(msg)
                return

        if dst in mac_to_port.get(dpid, {}):
            out_port = mac_to_port[dpid][dst]
            msg = of.ofp_flow_mod()
            msg.match = of.ofp_match.from_packet(packet, in_port)
            msg.priority = 50
            msg.idle_timeout = 0
            msg.hard_timeout = 0
            msg.actions.append(of.ofp_action_output(port=out_port))
            msg.data = event.ofp
            self.connection.send(msg)
            log.info("Installing flow: %s -> %s via port %d" % (src, dst, out_port))
        else:
            msg = of.ofp_packet_out()
            msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
            msg.data = event.ofp
            msg.in_port = in_port
            self.connection.send(msg)

def launch():
    def start_switch(event):
        BroadcastController(event.connection)
    core.openflow.addListenerByName("ConnectionUp", start_switch)
    log.info("Broadcast Traffic Controller launched")
