# Library for retrieving information from a Telstra Smart Modem.
# Based on scraping the web interface which takes a very long time to respond.
# It is the only way of retrieving infortmation from the modem without hacking it.

import ipaddress

import requests
import bs4

import telstra_smart_modem.srp as tsm_srp
import telstra_smart_modem.devices as tsm_devices
import telstra_smart_modem.exceptions as tsm_errors

HTTP_TIMEOUT = (3.05, 6)


class Modem():

	session = requests.Session()
	session.hooks = {
		'response': lambda r, *args, **kwargs: r.raise_for_status()
	}
	CSRFtoken = None

	def __init__(self, ip, username, password):
		host = ipaddress.IPv4Address(ip)
		self.base_url = f"http://{host}"
		self.username = username
		self.password = password

		self._authenticate()


	# Extract the CSRFtoken from html returned by one of the modem's web pages.
	def _extractCSRFtoken(self, html):
		soup = bs4.BeautifulSoup(html, 'html.parser')
		CSRFtoken = soup.head.find('meta', attrs={'name': 'CSRFtoken'})
		if CSRFtoken is not None:
			self.CSRFtoken = CSRFtoken['content']
		else:
			raise tsm_errors.TSMModemError("Expected CSRFtoken but didn't find one.")


	# Extract the CSRFtoken initially using html returned from the modem's index page.
	def _getCSRFtoken(self):
		index = self.session.get(self.base_url, timeout=HTTP_TIMEOUT)
		self._extractCSRFtoken(index.text)


	# Authenticate with the Modem using SRP.
	def _authenticate(self, html=None):
		
		def firstAuth(A: str):
			authenticate_first = self.session.post(
				f"{self.base_url}/authenticate",
				{
					"CSRFtoken": self.CSRFtoken,
					"I": self.username,
					"A": A
				},
				timeout=HTTP_TIMEOUT
			)
			first_response = authenticate_first.json()
			s = first_response['s']
			B = first_response['B']
			return s, B


		def secondAuth(M: str):
			authenticate_second = self.session.post(
				f"{self.base_url}/authenticate",
				{
					"CSRFtoken": self.CSRFtoken,
					"M": M
				},
				timeout=HTTP_TIMEOUT
			)
			second_response = authenticate_second.json()
			return second_response
		
		
		try:
			if html is not None:
				self._extractCSRFtoken(html)
			elif self.CSRFtoken is None:
				self._getCSRFtoken()

			srp = tsm_srp.User(self.username, self.password)
			A = srp.start_authentication()
			s, B = firstAuth(A)
			M = srp.process_challenge(s, B)
			second_response = secondAuth(M)
		
		except Exception as e:
			raise tsm_errors.TSMModemError(f"Error during authentication: {e}")

		# Check if password is correct
		recv_M = second_response.get('M')
		if recv_M is None:
			raise tsm_errors.TSMAuthError('Username and/or password is incorrect')


	# Logout of the modem. (For testing purposes)
	def _logout(self):
		try:
			logout = self.session.post(
				f"{self.base_url}/login.lp",
				{
					"do_signout": 1,
					"CSRFtoken": self.CSRFtoken
				},
				timeout=HTTP_TIMEOUT
			)
			_extractCSRFtoken(logout.text)
		except Exception as e:
			raise tsm_errors.TSMModemError(f"Error during logout: {e}")


	# Helper function to re-authenticate if timed-out.
	def _tryGet(self, modalFunction, exception, errorMessage):
		successful, data = modalFunction()

		if not successful:
			self._authenticate(data)
			successful, data = modalFunction()
			if not successful:
				raise exception(errorMessage)
		
		return data


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
			if html_table is None:
				return False, devices_response.text
			else:
				return True, html_table

		data = self._tryGet(
			getDeviceModal,
			tsm_errors.TSMModemError,
			"Failed to get clients from the modem."
		)
		return tsm_devices.Devices(data)


	# Return the status of the modem. (online, backup or offline)
	def getModemStatus(self):

		def getStatusModal():
			status_response = self.session.get(self.base_url, timeout=HTTP_TIMEOUT)
			soup = bs4.BeautifulSoup(status_response.text, 'html.parser')
			status = soup.find('div', attrs={
				"class": "message"
			})
			if status is None:
				return False, status_response.text
			else:
				return True, status

		def parseStatus(classname):
			if classname == "ok":
				return "online"
			elif classname == "backup":
				return "backup"
			elif classname == "error":
				return "offline"

		data = self._tryGet(getStatusModal, tsm_errors.TSMModemError, "Failed to get modem status.")

		img_class = data.find('img', attrs={
			"src": "img/status.png"
		})['class'][0]

		return parseStatus(img_class)
