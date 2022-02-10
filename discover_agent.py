import socket
import struct

class DiscoverAgent:
    def __init__(self, devices) -> None:
        self.devices = devices
        self.multicast_group = '239.255.255.250'
        self.server_address = ('', 1900)

        # Create the socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Bind to the server address
        self.sock.bind(self.server_address)

        # Tell the operating system to add the socket to the multicast group
        # on all interfaces.
        self.group = socket.inet_aton(self.multicast_group)
        self.mreq = struct.pack('4sL', self.group, socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, self.mreq)

    def discover(self):
        # Receive/respond loop
        while True:
            data, address = self.sock.recvfrom(512)
            ip, port = address
            data = data.decode('ascii')

            if 'M-SEARCH' in data:
                if 'urn:Belkin:device:**' in data or 'upnp:rootdevice' in data or 'ssdpsearch:all' in data or 'ssdp:all' in data:
                    for device in self.devices:
                        if 'urn:belkin:device:**' in data:     # type1 echo dot 2g, echo 1g's
                            type = 'urn:Belkin:device:**'
                        else:                                  # type2 Echo 2g (echo & echo plus)
                            type = 'upnp:rootdevice'
                        device.respond(ip, port, type)
