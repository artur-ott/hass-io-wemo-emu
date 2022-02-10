import yaml
import requests
import socket
from functools import partial
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

class WebServerRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, endpoint, name, persistent_uuid, uuid, state, *args, **kwargs):
        self.endpoint = endpoint
        self.name = name
        self.persistent_uuid = persistent_uuid
        self.uuid = uuid
        super().__init__(*args, **kwargs)

    def _set_response_xml(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/xml')
        self.end_headers()

    def _set_response_plain(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

    def do_GET(self):
        switcher = {
            "/": self.handleRoot,
            "/setup.xml": self.handleSetupXml,
            "/metainfoservice.xml": self.handleMetaInfoService,
            "/eventservice.xml": self.handleEventservice
        }

        switcher.get(self.path, self.handle404)()

    def do_POST(self):
        switcher = {
            "/upnp/control/basicevent1": self.handleUpnpControl
        }

        switcher.get(self.path, self.handle404)()

    def handle404(self):
        print('handle404({}: {}): {}'.format(str(self.headers), self.path, self.persistent_uuid))

    def handleRoot(self):
        pass

    def handleSetupXml(self):
        self._set_response_xml()
        print('handleSetupXml: {}'.format(self.persistent_uuid))
        state = 0
        response = """<?xml version="1.0"?>
<root xmlns="urn:Belkin:device-1-0">
    <specVersion>
    <major>1</major>
    <minor>0</minor>
    </specVersion>
    <device>
    <deviceType>urn:Belkin:device:controllee:1</deviceType>
    <friendlyName>{}</friendlyName>
    <manufacturer>Belkin International Inc.</manufacturer>
    <modelName>Emulated Socket</modelName>
    <modelNumber>3.1415</modelNumber>
    <manufacturerURL>http://www.belkin.com</manufacturerURL>
    <modelDescription>Belkin Plugin Socket 1.0</modelDescription>
    <modelURL>http://www.belkin.com/plugin/</modelURL>
    <UDN>uuid:{}</UDN>
    <serialNumber>{}</serialNumber>
    <binaryState>{}</binaryState>
    <serviceList>
        <service>
            <serviceType>urn:Belkin:service:basicevent:1</serviceType>
            <serviceId>urn:Belkin:serviceId:basicevent1</serviceId>
            <controlURL>/upnp/control/basicevent1</controlURL>
            <eventSubURL>/upnp/event/basicevent1</eventSubURL>
            <SCPDURL>/eventservice.xml</SCPDURL>
        </service>
        <service>
          <serviceType>urn:Belkin:service:metainfo:1</serviceType>
          <serviceId>urn:Belkin:serviceId:metainfo1</serviceId>
          <controlURL>/upnp/control/metainfo1</controlURL>
          <eventSubURL>/upnp/event/metainfo1</eventSubURL>
          <SCPDURL>/metainfoservice.xml</SCPDURL>
        </service>
    </serviceList>
    </device>
</root>\r\n\r\n""".format(self.name, self.persistent_uuid, self.uuid, state)

        self.wfile.write(response.encode('ascii'))

    def handleUpnpControl(self):
        self._set_response_xml()
        print('handleUpnpControl: {}'.format(self.persistent_uuid))
        method = 'GetBinaryStateResponse'
        state = self.getStateFromEndpoint()
        content_len = int(self.headers.get('Content-Length'))
        body = self.rfile.read(content_len).decode('ascii')

        if 'SetBinaryState' in body:
            method = 'SetBinaryStateResponse'
            if '<BinaryState>0</BinaryState>' in body and int(state) != 0:
                self.setStateFromEndpoint(0)
                state = 0
            elif '<BinaryState>1</BinaryState>' in body and int(state) != 1:
                self.setStateFromEndpoint(1)
                state = 1

        response = '\r\n'.join("""<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <s:Body>
        <u:{} xmlns:u="urn:Belkin:service:basicevent:1">
        <BinaryState>{}</BinaryState>
        </u:{}>
    </s:Body>
</s:Envelope>

""".format(method, state, method).splitlines())

        self.wfile.write(response.encode('ascii'))

    def handleEventservice(self):
        self._set_response_xml()
        print('handleEventservice: {}'.format(self.persistent_uuid))
        response = """<scpd xmlns="urn:Belkin:service-1-0">
<actionList>
    <action>
    <name>SetBinaryState</name>
    <argumentList>
        <argument>
        <retval/>
        <name>BinaryState</name>
        <relatedStateVariable>BinaryState</relatedStateVariable>
        <direction>in</direction>
        </argument>
    </argumentList>
    </action>
    </actionList>
        <serviceStateTable>
        <stateVariable sendEvents="yes">
        <name>BinaryState</name>
        <dataType>Boolean</dataType>
        <defaultValue>0</defaultValue>
        </stateVariable>
    </serviceStateTable>
</scpd>\r\n\r\n"""

        self.wfile.write(response.encode('ascii'))

    def handleMetaInfoService(self):
        self._set_response_plain()
        print('handleMetaInfoService: {}'.format(self.persistent_uuid))
        response = """<scpd xmlns="urn:Belkin:service-1-0">
<specVersion>
    <major>1</major>
    <minor>0</minor>
</specVersion>
<actionList>
    <action>
    <name>GetMetaInfo</name>
    <argumentList>
        <retval />
        <name>GetMetaInfo</name>
        <relatedStateVariable>MetaInfo</relatedStateVariable>
        <direction>in</direction>
    </argumentList>
    </action>
</actionList>
<serviceStateTable>
    <stateVariable sendEvents="yes">
    <name>MetaInfo</name>
    <dataType>string</dataType>
    <defaultValue>0</defaultValue>
    </stateVariable>
</serviceStateTable>
</scpd>\r\n\r\n"""

        self.wfile.write(response.encode('ascii'))

    def getStateFromEndpoint(self):
        request =requests.get(self.endpoint)
        if request.status_code == 200:
            return request.text.strip()
        else:
            print("Endpoint response is not 200: {}".format(request.status_code))
            return 0

    def setStateFromEndpoint(self, state):
        request = requests.post(self.endpoint, str(state).encode('ascii'))

class Device(yaml.YAMLObject):
    yaml_tag = '!device'
    def __init__(self, name, port, endpoint, ip) -> None:
        super().__init__()
        self.name = name
        self.localIp = ip
        self.port = port
        self.endpoint = endpoint
        self.uuid = '38323636-4558-4dda-9188-cda0e6{}{}{}'.format( #
            Device._convert_to_hex(port >> 16), #
            Device._convert_to_hex(port >> 8), #
            Device._convert_to_hex(port & 0xff))
        self.persistent_uuid = "Socket-1_0-" + self.uuid + "-" + str(self.port)
        self._webserverThread = Thread(target = self._startServer)
        self._webserverThread.start()

    def respond(self, ip, port, type):
        print('{} respond search device to {}'.format(self.persistent_uuid, str((ip, port))))
        response = '\r\n'.join("""HTTP/1.1 200 OK
CACHE-CONTROL: max-age=86400
DATE: Sat, 26 Nov 2016 04:56:29 GMT
EXT:
LOCATION: http://{}:{}/setup.xml
OPT: "http://schemas.upnp.org/upnp/1/0/"; ns=01
01-NLS: b9200ebb-736d-4b93-bf03-835149d13983
SERVER: Unspecified, UPnP/1.0, Unspecified
ST: {}
USN: uuid:{}::{}
X-User-Agent: redsonic

""".format(self.localIp, str(self.port), type, self.persistent_uuid, type).splitlines())

        print('Resp: {}'.format(response))

        udp_address = (ip, port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(bytes(response, 'ascii'), udp_address)

    def _startServer(self, server_class=HTTPServer, handler_class=WebServerRequestHandler):
        print('Device started at {}'.format(str((self.localIp, self.port))))
        address = ('', self.port)
        state = [0]
        handler_class = partial(handler_class, self.endpoint,
            self.name, self.persistent_uuid, self.uuid, state)
        httpd = server_class(address, handler_class)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        httpd.server_close()

    def _convert_to_hex(number):
        string = '{:02X}'.format(number & 0xff)
        if len(string.strip()) < 2:
            string = '0' + string.strip()
        return string
