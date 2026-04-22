from pox.core import core
import pox.openflow.libopenflow_01 as of

log = core.getLogger()

H1 = "00:00:00:00:00:01"
H3 = "00:00:00:00:00:03"

class AccessControl(object):
    def __init__(self, connection):
        self.connection = connection
        connection.addListeners(self)

    def add_flow(self, match, actions):
        msg = of.ofp_flow_mod()
        msg.match = match
        msg.actions = actions
        self.connection.send(msg)

    def _handle_PacketIn(self, event):
        packet = event.parsed

        if not packet.parsed:
            return

        src = str(packet.src)
        dst = str(packet.dst)

        log.info(f"{src} -> {dst}")

        # 🚫 BLOCK h1 <-> h3
        if (src == H3 and dst == H1) or (src == H1 and dst == H3):
            log.warning("BLOCKED h1 <-> h3")

            match = of.ofp_match(dl_src=packet.src, dl_dst=packet.dst)
            self.add_flow(match, [])  # DROP
            return

        # ✅ ALLOW (FLOOD for learning)
        match = of.ofp_match(dl_src=packet.src, dl_dst=packet.dst)
        actions = [of.ofp_action_output(port=of.OFPP_FLOOD)]

        self.add_flow(match, actions)

        # send packet
        msg = of.ofp_packet_out()
        msg.data = event.ofp
        msg.actions = actions
        self.connection.send(msg)


# Connection logs
def _handle_ConnectionUp(event):
    print("🔗 Switch connected")

def _handle_ConnectionDown(event):
    print("❌ Connection closed")


def launch():
    core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
    core.openflow.addListenerByName("ConnectionDown", _handle_ConnectionDown)

    def start_switch(event):
        AccessControl(event.connection)

    core.openflow.addListenerByName("ConnectionUp", start_switch)
