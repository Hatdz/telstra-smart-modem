# Library for retrieving information from a Telstra Smart Modem.
# Based on scraping the web interface which takes a very long time to respond.
# It is the only way of retrieving information from the modem without hacking it.

import telstra_smart_modem.devices as tsm_devices
from telstra_smart_modem.base import *


class Modem(ModemBase):

    # Return a Devices object of all devices seen by the modem.
    def getDevices(self):

        def getDeviceModal():
            devices_response = self.session.get(
                f"{self.base_url}/modals/device-modal.lp",
                timeout=HTTP_TIMEOUT
            )
            soup = bs4.BeautifulSoup(devices_response.text, 'html.parser')
            html_table = soup.find('table', attrs={
                "id": "devices",
                "class": "table table-striped"
            })
            if html_table:
                return True, html_table
            else:
                return False, soup

        data = self._tryGet(getDeviceModal, "Failed to get clients from the modem")
        return tsm_devices.Devices(data)

    # Return the status of the modem. (online, backup or offline)
    def getModemStatus(self):

        def getStatusModal():
            response = self.session.get(self.base_url, timeout=HTTP_TIMEOUT)
            soup = bs4.BeautifulSoup(response.text, 'html.parser')
            status = soup.find('img', attrs={"src": "img/status.png"})
            if status:
                self._extractCSRFtoken(soup)
                return True, status
            else:
                return False, soup

        def parseStatus(classname):
            switch = {
                "ok": "online",
                "backup": "backup",
                "error": "offline"
            }
            return switch.get(classname, "unknown")

        img = self._tryGet(getStatusModal, "Failed to get modem status")
        return parseStatus(img['class'][0])
