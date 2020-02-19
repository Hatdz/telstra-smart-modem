# Class to represent the devices connected to or seen by the modem.
# This class is returned from Modem.getclients() and can't be used by itself.

import re
import bs4

# Compiled regular expressions:
re_mac = re.compile(r"(?:[0-9a-f]{2}[:]){5}[0-9a-f]{2}")
re_ipv4 = re.compile(r"(?:[0-9]{1,3}[.]){3}[0-9]{1,3}")
re_ipv6_full = re.compile(r"(?:[0-9a-f]{1,4}:){7}[0-9a-f]{1,4}")


class Devices():

	def __init__(self, html):
		self.devices = self._parse(html)

	# Parse the html table from Modem.getclients()
	def _parse(self, html):

		headers = ['online', 'hostname', 'ip', 'mac', 'connection', 'eth-port']

		def parseOnlineStatus(td: bs4.element.Tag) -> bool:
			status = td.div['class'][1]
			if status == "green":
				return True
			else:
				return False
		
		def parseEthPort(possiblePort: str):
			if possiblePort is not None:
				return int(possiblePort)

		def parseIPV4(ips: str):
			if ips is not None:
				match = re_ipv4.search(ips)
				if match is not None:
					return match.group()

		def parseIPV6(ips: str):
			if ips is None:
				return []
			else:
				return re_ipv6_full.findall(ips)


		html_table = html.tbody.find_all('tr')

		devices = []

		for row in html_table:
			cols = row.find_all('td')
			device = {}
			for index, item in enumerate(cols):
				header = headers[index]

				if index == 0:
					device[header] = parseOnlineStatus(item)
				elif index == 2:
					device['ipv4'] = parseIPV4(item.string)
					device['ipv6'] = parseIPV6(item.string)
				elif index == 5:
					device[header] = parseEthPort(item.string)
				else:
					device[header] = item.string

			devices.append(device)

		return devices

	# Validate a supplied MAC address and convert it to the correct format.
	def validMAC(self, mac: str) -> str:
		valid_mac = mac.lower()
		valid_mac = valid_mac.replace("-", ":", 5)

		if re_mac.fullmatch(valid_mac) is None:
			raise ValueError(f"Invalid MAC address: '{mac}'")

		return valid_mac

	# Get a specific device's details from a MAC address.
	def getDevice(self, mac: str) -> dict:
		valid_mac = self.validMAC(mac)
		for device in self.devices:
			if device['mac'] == valid_mac:
				return device

	# Check if a device is connected to the modem by MAC address.
	def isOnline(self, mac: str) -> bool:
		device = self.getDevice(mac)
		if device is None:
			return False
		else:
			return device['online']
