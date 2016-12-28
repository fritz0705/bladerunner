# coding: utf-8

import libvirt
import lxml.etree
import urllib.parse
import jinja2

class DomainDescription(object):
    _xml = None
    def __init__(self, domain):
        self.domain = domain

    @property
    def xml(self):
        if self._xml is None:
            self._xml = lxml.etree.fromstring(self.domain.XMLDesc())
        return self._xml

    def flush_cache(self):
        self._xml = None

    @property
    def memory(self):
        return self.memory_in(1024 * 1024)

    def memory_in(self, multiplier):
        node = self.xml.find("./memory")
        unit = node.get("unit")
        value = node.text
        mult = {
            "KiB": 1024,
            "MiB": 1024 * 1024,
            "GiB": 1024 * 1024 * 1024,
            "KB": 1000,
            "MB": 1000 * 1000,
            "GB": 1000 * 1000 * 1000
        }[unit]/multiplier

        return int(value)*mult

    @property
    def vcpus(self):
        return int(self.xml.find("./vcpu").text)

    def features(self):
        return (node.tag for node in self.xml.findall("./features/*"))
    
    @property
    def vnc_port(self):
        node = self.xml.find("./devices/graphics[@type='vnc']")
        if not node or not node.get("port"):
            return None
        return int(node.get("port"))
    
    @property
    def spice_port(self):
        node = self.xml.find("./devices/graphics[@type='spice']")
        if not node or not node.get("port"):
            return None
        return int(node.get("port"))
    
    def remote_management_uri(self, host=None):
        url_scheme = None
        port = None
        if self.spice_port:
            url_scheme = "spice"
            port = self.spice_port
        elif self.vnc_port:
            url_scheme = "vnc"
            port = self.vnc_port
        if url_scheme is None:
            return None
        if ":" in host:
            host = "[{}]".format(host)
        return urllib.parse.urlunparse((url_scheme, "{}:{}".format(host, port),
            "/", "", "", ""))

    @property
    def cdrom(self):
        node = self.xml.find("./devices/disk[@device='cdrom']")
        if not node:
            return None
        node = node.find("./source")
        if not node:
            return None
        return (node.get("pool"), node.get("volume"))

    @cdrom.setter
    def cdrom(self, new_medium):
        pool, vol = new_medium
        n = self.cdrom_node
        src_node = n.find("./source")
        if not src_node:
            element = lxml.etree.SubElement(n, "source")
            element.set("pool", pool)
            element.set("volume", vol)
            return
        else:
            node.set("pool", pool)
            node.set("volume", vol)
        target_node = n.find("./target")
        if target_node:
            target_node.set("tray", "closed")

    @cdrom.deleter
    def cdrom(self):
        n = self.cdrom_node
        if n:
            n.find("target").set("tray", "open")
    
    @property
    def has_cdrom(self):
        return self.xml.find("./devices/disk[@device='cdrom']") is not None

    @property
    def cdrom_node(self):
        return self.xml.find("./devices/disk[@device='cdrom']")

    def dump(self):
        return lxml.etree.dump(self.xml)

class VirtualMachineTemplate(object):
    def __init__(self, loader=None):
        if loader is None:
            loader = jinja2.PackageLoader("yolocloud", "templates")
        self.jinja2_env = jinja2.Environment(loader=loader)

    def render_template(self, name, *args, **kwargs):
        return self.jinja2_env.get_template(name).render(*args, **kwargs)

    def provision(self, vm, vir_conn):
        pass

class BaseVMTemplate(VirtualMachineTemplate):
    def __init__(self, memory=1024, hdd=1024*10, network_bridge="virbr1",
            network_type="e1000", with_network=True, with_cdrom=True, cpus=1):
        VirtualMachineTemplate.__init__(self)
        self.memory = memory
        self.cpus = cpus
        self.hdd = hdd
        self.network_bridge = network_bridge
        self.network_type = network_type
        self.with_network = with_network
        self.with_cdrom = with_cdrom

    def provision(self, vm, vir_conn):
        domain_xml = self.render_template("base/domain.xml", memory=self.memory,
                cpus=self.cpus, hdd=self.hdd, network_bridge=self.network_bridge,
                network_type=self.network_type, with_network=self.with_network,
                with_cdrom=self.with_cdrom, vm=vm)
        volume_xml = self.render_template("base/volume.xml", memory=self.memory,
                cpus=self.cpus, hdd=self.hdd, network_bridge=self.network_bridge,
                network_type=self.network_type, with_network=self.with_network,
                with_cdrom=self.with_cdrom, vm=vm)
        vir_conn.defineXML(domain_xml)
        default_pool = vir_conn.storagePoolLookupByName("default")
        default_pool.createXML(volume_xml)
    
    def __str__(self):
        return "Barebone image ({} MB RAM, {} GB HDD, {} CPUs)".format(
                self.memory, self.hdd, self.cpus)

state_to_text_mapping = {
    libvirt.VIR_DOMAIN_NOSTATE: "No State",
    libvirt.VIR_DOMAIN_RUNNING: "Running",
    libvirt.VIR_DOMAIN_BLOCKED: "Blocked",
    libvirt.VIR_DOMAIN_PAUSED: "Paused",
    libvirt.VIR_DOMAIN_SHUTDOWN: "Shutting down",
    libvirt.VIR_DOMAIN_SHUTOFF: "Shutdown",
    libvirt.VIR_DOMAIN_CRASHED: "Crashed",
    libvirt.VIR_DOMAIN_PMSUSPENDED: "Suspended by power management"
}
