# Custom exception classes

class TSMBase(Exception):
	"""Base class for the Telstra Smart Modem"""

class TSMAuthError(TSMBase):
	"""Errors relating to authentication"""

class TSMModemError(TSMBase):
	"""Errors relating to the modem not working correctly"""
