# Base class for the modem object providing authentication, logout and helper
# methods for ensuring the connection to the modem remains authenticated.

import ipaddress

import bs4
import requests

import telstra_smart_modem.exceptions as tsm_errors
import telstra_smart_modem.srp as tsm_srp

HTTP_TIMEOUT = (3.05, 6)


class ModemBase:

    session = requests.Session()
    session.hooks = {
        # Always raise for status when making a request to the modem:
        'response': lambda r, *args, **kwargs: r.raise_for_status()
    }
    CSRFtoken = None

    def __init__(self, ip: str, username: str, password: str, _init_authenticate: bool = True):
        host = ipaddress.IPv4Address(ip)
        self.base_url = f"http://{host}"
        self.username = str(username)
        self.password = str(password)

        if _init_authenticate:
            self._authenticate()

    # Get the session id used for authentication.
    def _get_sessionID(self) -> str:
        return self.session.cookies.get('sessionID')

    # Set the session id.
    def _set_sessionID(self, sessionID: str) -> None:
        self.session.cookies['sessionID'] = sessionID

    # Extract the CSRFtoken from soup.
    def _extractCSRFtoken(self, soup):
        CSRFtoken = soup.find('meta', attrs={'name': 'CSRFtoken'})
        if CSRFtoken:
            self.CSRFtoken = CSRFtoken['content']
        else:
            raise tsm_errors.TSMModemError("Expected CSRFtoken but didn't find one")

    # Extract the CSRFtoken from raw html.
    def _extractCSRFtoken_html(self, html):
        strainer = bs4.SoupStrainer('meta')
        soup = bs4.BeautifulSoup(html, 'html.parser', parse_only=strainer)
        self._extractCSRFtoken(soup)

    # Extract the CSRFtoken from the modem index page.
    def _getCSRFtoken(self):
        response = self.session.get(self.base_url, timeout=HTTP_TIMEOUT)
        self._extractCSRFtoken_html(response.text)

    # Authenticate with the Modem using SRP.
    def _authenticate(self, soup=None):

        def authRequest(data):
            r = self.session.post(
                f"{self.base_url}/authenticate",
                {**{"CSRFtoken": self.CSRFtoken}, **data},
                timeout=HTTP_TIMEOUT
            )
            return r.json()

        def firstAuthRequest(A):

            def doFirstAuth():
                return authRequest({"I": self.username, "A": A})

            try:
                r = doFirstAuth()
            except requests.exceptions.HTTPError as ex:
                status = ex.response.status_code
                if status == 403:
                    self._getCSRFtoken()
                    r = doFirstAuth()
                else:
                    raise

            s = r.get('s')
            B = r.get('B')
            if not (s and B):
                raise tsm_errors.TSMUsernameIncorrect('Username is incorrect')

            return s, B

        def secondAuthRequest(M):
            r = authRequest({"M": M})
            M = r.get('M')
            if not M:
                raise tsm_errors.TSMPasswordIncorrect('Password is incorrect')

        def doAuth():
            srp = tsm_srp.User(self.username, self.password)
            A = srp.start_authentication()
            s, B = firstAuthRequest(A)
            M = srp.process_challenge(s, B)
            secondAuthRequest(M)

        try:
            if soup:
                self._extractCSRFtoken(soup)
            elif not self.CSRFtoken:
                self._getCSRFtoken()

            try:
                doAuth()
            except tsm_errors.TSMPasswordIncorrect:
                # Attempt authentication one more time if failed.
                # This is due to an extremely low probability error that occurs in srp.py.
                doAuth()

        except tsm_errors.TSMPasswordIncorrect as e:
            raise e from None

        except tsm_errors.TSMBase:
            raise

        except Exception as e:
            raise tsm_errors.TSMModemError(f"Error during authentication: {type(e)} | {e}")

    # Helper function to re-authenticate if timed-out.
    def _tryGet(self, modalFunction, errorMessage):
        try:
            successful, data = modalFunction()

            if not successful:
                self._authenticate(data)
                successful, data = modalFunction()
                if not successful:
                    raise tsm_errors.TSMModemError(errorMessage)

            return data

        except tsm_errors.TSMBase:
            raise

        except Exception as e:
            raise tsm_errors.TSMModemError(f"{errorMessage} {type(e)} | {e}")

    # Logout of the modem. (For testing purposes)
    def _logout(self):

        def doLogout():
            response = self.session.post(
                f"{self.base_url}/login.lp",
                {"do_signout": 1, "CSRFtoken": self.CSRFtoken},
                timeout=HTTP_TIMEOUT
            )
            self._extractCSRFtoken_html(response.text)

        try:
            try:
                doLogout()
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code
                if status == 403:
                    self._getCSRFtoken()
                    doLogout()
                else:
                    raise

        except Exception as e:
            raise tsm_errors.TSMModemError(f"Error during logout: {type(e)} | {e}")
