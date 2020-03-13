# Class with helper methods to represent the devices connected to or seen by the modem.
# This class is returned from Modem.getDevices() and can't be used by itself.

import ipaddress
import re
import bs4

# Compiled regular expressions:
re_mac = re.compile(r"(?:[0-9a-f]{2}[:]){5}[0-9a-f]{2}")
re_ipv4 = re.compile(r"(?:[0-9]{1,3}[.]){3}[0-9]{1,3}")
re_ipv6_full = re.compile(r"(?:[0-9a-f]{1,4}:){7}[0-9a-f]{1,4}")


# Parse the html table from Modem.getDevices()
def parseDevices(soup):
    headers = ['online', 'hostname', 'ip', 'mac', 'connection', 'eth-port']

    def extractOnlineStatus(td: bs4.element.Tag) -> bool:
        status = td.div['class'][1]
        if status == "green":
            return True
        else:
            return False

    def extractEthPort(possiblePort: str):
        if possiblePort:
            return int(possiblePort)

    def extractIPV4(ips: str):
        if ips:
            ipv4 = re_ipv4.findall(ips)
            if ipv4:
                return ipaddress.IPv4Address(ipv4[0])

    def extractIPV6(ips: str):
        if ips:
            ipv6s = re_ipv6_full.findall(ips)
            return [ipaddress.IPv6Address(ipv6) for ipv6 in ipv6s]
        else:
            return []

    html_table = soup.tbody.find_all('tr')
    devices = []

    for row in html_table:
        cols = row.find_all('td')
        device = {}
        for index, item in enumerate(cols):
            header = headers[index]

            if index == 0:
                device[header] = extractOnlineStatus(item)
            elif index == 2:
                device['ipv4'] = extractIPV4(item.string)
                device['ipv6'] = extractIPV6(item.string)
            elif index == 5:
                device[header] = extractEthPort(item.string)
            else:
                device[header] = item.string

        devices.append(device)

    return devices


# Validate a supplied MAC address and convert it to the correct format.
def validateMAC(mac: str) -> str:
    valid_mac = mac.lower()
    valid_mac = valid_mac.replace("-", ":", 5)
    if not re_mac.fullmatch(valid_mac):
        raise ValueError(f"Invalid MAC address: '{mac}'")

    return valid_mac


class Devices:

    def __init__(self, soup):
        self.devices = parseDevices(soup)

    # Get a specific device's details from it's MAC address.
    def getDevice(self, mac: str) -> dict:
        valid_mac = validateMAC(mac)
        for device in self.devices:
            if device['mac'] == valid_mac:
                return device

    # Check if a device is currently connected to the modem by MAC address.
    def isOnline(self, mac: str) -> bool:
        device = self.getDevice(mac)
        if device:
            return device['online']
        else:
            return False
