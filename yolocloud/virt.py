# coding: utf-8

import libvirt
import lxml.etree

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

state_to_text_mapping = {
    libvirt.VIR_DOMAIN_NOSTATE: "No state",
    libvirt.VIR_DOMAIN_RUNNING: "Running",
    libvirt.VIR_DOMAIN_BLOCKED: "Blocked",
    libvirt.VIR_DOMAIN_PAUSED: "Paused",
    libvirt.VIR_DOMAIN_SHUTDOWN: "Shut down",
    libvirt.VIR_DOMAIN_SHUTOFF: "Shut off",
    libvirt.VIR_DOMAIN_CRASHED: "Crashed",
    libvirt.VIR_DOMAIN_PMSUSPENDED: "Suspended by power management"
}
