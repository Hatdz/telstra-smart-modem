# Non standard implementation of the SRP protocol that Telstra/Technicolor
# uses for the smart modem gen 2 and possibly other Technicolor routers as well. Since
# I couldn't get any Python SRP libraries working correctly, this implementation is
# reverse engineered from srp-min.js (sent from the modem). It only functions as a client/user.

import hashlib
import random

# Convert Int to hex string
def toHex(number: int) -> str:
	hexString = format(number, 'x')
	if 1 == len(hexString) % 2:
		hexString = '0' + hexString
	return hexString

# SHA256 hash helper
def hash(value: bytes, outformat: str = 'HEX'):
	h = hashlib.sha256()
	h.update(value)
	if outformat == 'BIN':
		return h.digest()
	elif outformat == 'INT':
		return int.from_bytes(h.digest(), byteorder='big')
	else:
		return h.hexdigest()

# Calculate the 'u' variable in SRP
def calculate_u(A: str, B: str) -> int:
	A_bytes = A.to_bytes(256, 'big', signed=False)
	B_bytes = B.to_bytes(256, 'big', signed=False)
	hashed = hash(A_bytes + B_bytes, outformat='INT')
	return hashed

# Get Random integer for the 'a' client variable in SRP
def getRandomA() -> int:
	return random.SystemRandom().getrandbits(2048) % N


# Shared SRP variables:
g = 2
N = '''
ac6bdb41324a9a9bf166de5e1389582faf72b6651987ee07fc3192943db56050a37329cbb4a099ed8193e0757767a13dd52312ab4b03310d
cd7f48a9da04fd50e8083969edb767b0cf6095179a163ab3661a05fbd5faaae82918a9962f0b93b855f97993ec975eeaa80d740adbf4ff74
7359d041d5c33ea71d281e446b14773bca97b43a23fb801676bd207a436c6481f1d2b9078717461a5b9d32e688f87748544523b524b0d57d
5ea77a2775d2ecfa032cfbdbf52fb3786160279004e57ae6af874e7303ce53299ccc041c7bc308d82a5698f3a8d0c38271ae35f8e9dbfbb6
94b5c803d89f7ae435de236d525f54759b65e372fcd68ef20fa7111f9e4aff73
'''
N = N.replace(" ", "").replace("\n", "")
N = int(N, 16)

# Magic numbers:
magic_C = '05b9e8ef059c6b32ea59fc1d322d37f04aa30bae5aa9003b8321e21ddb04e300'
magic_C = int(magic_C, 16)
# This one stays in hex format. Likely some kind of shared secret.
magic_u = '4a76a9a2402bdd18123389b72ebbda50a30f65aedb90d7273130edea4b29cc4c'

# SRP User class for authenticating with the Telstra Smart Modem.
class User:

	def __init__(self, username: str, password: str):
		self.username = username
		self.password = password

	# Return the calculated 'A' variable in SRP to send to the server.
	def start_authentication(self) -> str:
		self.a = getRandomA()

		A = 0
		while A == 0:
			A = pow(g, self.a, N)

		self.A = A
		self.A_hex = toHex(A)
		return self.A_hex

	# Take the 's' and 'B' SRP variables from the server and calculate 
	# the 'M' SRP variable to send back to the server.
	def process_challenge(self, s_hex: str, B_hex: str) -> str:
		B = int(B_hex, 16)
		u = calculate_u(self.A, B)

		user_pass = hash(f"{self.username}:{self.password}".encode())
		n = hash(bytes.fromhex(s_hex + user_pass), 'INT')

		mya = (magic_C * pow(g, n, N)) % N
		myb = (self.a + ((u * n) % N)) % N
		mye = pow(((B - mya) % N), myb, N)

		mye_bytes = mye.to_bytes(256, byteorder='big')

		_B = hash(mye_bytes)
		_e = hash(self.username.encode())
		M = hash(bytes.fromhex(magic_u + _e + s_hex + self.A_hex + B_hex + _B))
		return M
