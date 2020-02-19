# Telstra Smart Modem - Python library

This library provides a Python 3 interface to query information from a Telstra Smart Modem (Gen 2).

## Tested with

* Telstra Smart Modem (Gen 2):
	* **Model**: Technicolor DJA0231
	* **Firmware**: 18.1.c.0443-950-RB

## Current features

* Retrieving online status (Online, Backup & Offline)
* Retrieving connected devices:
	* Checking if a device is connected
	* Retrieving information of seen device's
	(ipv4, ipv6, hostname, mac, connection type, ethernet port)

## Links

* [GitHub](https://github.com/hatdz/telstra-smart-modem/)
* [PyPi](https://pypi.org/project/telstra-smart-modem/)

## Installation

### Requirements

* [Requests](https://pypi.org/project/requests/)
* [Beautiful Soup](https://pypi.org/project/beautifulsoup4/)

### Methods

#### PIP

```
pip install telstra-smart-modem
```

## Usage

### Initialization

```python
import telstra_smart_modem

IP = '192.168.0.1'
USERNAME = 'admin'
PASSWORD = 'Telstra'

# Create tsm (Telstra Smart Modem) modem object:
tsm = telstra_smart_modem.Modem(IP, USERNAME, PASSWORD)
```

### Devices

```python
# Get current devices object from modem:
>>> clients = tsm.getDevices()

# Get list of seen devices:
>>> clients.devices
[
	{
		'online': False,
		'hostname': 'host1',
		'ipv4': None,
		'ipv6': [],
		'mac': '00:00:00:00:00:01',
		'connection': 'wireless - 5GHz',
		'eth-port': None
	},
	{
		'online': True,
		'hostname': 'host2',
		'ipv4': '192.168.0.3',
		'ipv6': [
			'2001:0db8:0000:0000:0000:8a2e:0370:7334'
		],
		'mac': '00:00:00:00:00:02',
		'connection': 'ethernet',
		'eth-port': 2
	}
]

# Get specific device by mac address:
>>> clients.getDevice("00:00:00:00:00:01")
{
	'online': False,
	'hostname': 'host1',
	'ipv4': None,
	'ipv6': [],
	'mac': '00:00:00:00:00:01',
	'connection': 'ethernet',
	'eth-port': 2
}

# Check if a device is currently connected:
>>> clients.isOnline("00:00:00:00:00:02")
True
>>> clients.isOnline("11:11:11:11:11:11")
False
```

### Online status

```python
# Returns 'online' if the modem is connected through the WAN port.
# Returns 'backup' if the WAN connection is down and the 4G backup is active.
# Returns 'offline' if both the WAN and 4G connections are down.

>>> tsm.getModemStatus()
online
```