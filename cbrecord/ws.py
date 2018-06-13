"""Fetches data from the website.

Fuctions:
    - make_request: Fetch HTML from the given url.
    - is_logged_in: Check if the user is logged in to CB.
    - login: Try to log in to CB.
    - get_models: Get a list of online followed models who are free to watch.
    - requests_retry_session: Wrap a requests session with retries.
    - get_request: Send a GET request wrapped in retries.
    - post_request: Send a POST request wrapped in retries.
"""

import json
import logging
import os
import requests
import time

from base64 import b64decode
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from cbrecord import const


def make_request(cbr, url, initial_login=False):
    """Fetch HTML from the given url.

    Parameters:
        - cbr (object): The run session object (CBRecord class).
        - url (string): The url to get HTML from.
        - initial_login (bool): True if first login attempt.

    Returns:
        - string: The HTML code requested from the given url.
    """
    logger = logging.getLogger(__name__ + ".make_request")
    request = None
    cookie = {}
    already_logged_in = True

    try:
        if os.path.isfile(const.CONFIG_DIR + const.COOKIE_FN):
            with open(const.CONFIG_DIR + const.COOKIE_FN, 'r') as f:
                cookie = requests.utils.cookiejar_from_dict(json.load(f))
    except json.JSONDecodeError:
        logger.warning("Cookie file error.")

    while request is None:
        request = get_request(cbr, url, cookie)

        while (request is not None) and (is_logged_in(request.text) is False):
            already_logged_in = False
            login(cbr)
            request = get_request(cbr, url, cookie)

    if (already_logged_in is True) and (initial_login is True):
        logger.info("Already logged in.")
    return request.text


def is_logged_in(html):
    """Check if the user is logged in to CB.

    Parameters:
        - html (string): The HTML code of a CB request.

    Returns:
        - bool: True if the user is logged in.
    """
    soup = BeautifulSoup(html, "html.parser")

    if soup.find('div', {'id': 'user_information'}) is None:
        return False
    else:
        return True


def login(cbr):
    """Try to log in to CB.

    Parameters:
        - cbr (object): The run session object (CBRecord class).
    """
    logger = logging.getLogger(__name__ + ".login")
    url = b64decode(b'aHR0cHM6Ly9jaGF0dXJiYXRlLmNvbS' +
                    b'9hdXRoL2xvZ2luLz9uZXh0PS8=').decode("utf-8")

    request = get_request(cbr, url)

    soup = BeautifulSoup(request.text, 'html.parser')
    csrf = soup.find('input', {'name': 'csrfmiddlewaretoken'}).get('value')
    agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36' \
            '(KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
    data = {
        'csrfmiddlewaretoken': csrf,
        'username': cbr.cbr_config['username'],
        'password': cbr.cbr_config['password'],
        'rememberme': 'on',
        'next': '/',
    }
    headers = {
        'user-agent': agent,
        'Referer': url
    }

    request = post_request(cbr, url, data, headers, cookie=request.cookies)

    if is_logged_in(request.text) is True:
        with open(const.CONFIG_DIR + const.COOKIE_FN, 'w+') as f:
            json.dump(requests.utils.dict_from_cookiejar(request.cookies), f)
        logger.info("Login successful as: {}".format(
            cbr.cbr_config['username']))
    else:
        logger.warning("Login failed as: {}".format(
            cbr.cbr_config['username']))
        print("Wrong user credentials or too many login attempts.")
        raise SystemExit(0)


def get_models(cbr):
    """Get a list of online followed models who are free to watch.

    Parameters:
        - cbr (object): The run session object (CBRecord class).

    Returns:
        - list: A list of online followed models who are free to watch.
    """
    logger = logging.getLogger(__name__ + ".get_models")
    url = b64decode(b'aHR0cHM6Ly9jaGF0dXJiYXR' +
                    b'lLmNvbS9mb2xsb3dlZC1jYW1zLw==').decode("utf-8")
    html = make_request(cbr, url)
    models = []

    try:
        soup = BeautifulSoup(html, "html.parser")
        models_ul = soup.find('ul', {'class': 'list'})
        models_li = models_ul.findAll('li', recursive=False)

        for model in models_li:
            model_name = model.find('a')['href'].replace('/', '')

            offline = model.find('div', {'class': 'thumbnail_label_offline'})
            private = model.find('div', {'class':
                                         'thumbnail_label_c_private_show'})
            group = model.find('div', {'class':
                                       'thumbnail_label_c_group_show'})

            if (offline or private or group):
                continue

            models.append(model_name)
    except (AttributeError, KeyError):
        logger.error("No followed models error.")
        raise SystemExit(1)

    return models


def requests_retry_session(
    session,
    retries=4,
    backoff_factor=0.4,
    status_forcelist=(500, 502, 503, 504)
):
    """Wrap a requests session with retries.

    Parameters:
        - session (Session): A Session object to manage and persist settings
          across requests.
        - retries (int): Number of retries to allow for total, connect or read.
        - backoff_factor (float): A backoff factor to apply between attempts
          after the second try.
        - status_forcelist (iterable): A set of integer HTTP status codes that
          we should force a retry on.

    Returns:
        - Session: A Session object to manage and persist settings across
          requests.
    """
    session = session
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        method_whitelist=frozenset(['GET', 'POST'])
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    return session


def get_request(cbr, url, cookie=None):
    """Send a GET request wrapped in retries.

    Parameters:
        - cbr (CBRecord): The run session object.
        - url (str): URL for the Session object.
        - cookie (CookieJar): A CookieJar containing all cookies to set on the
          session.

    Returns:
        - Response object: The server’s response to the HTTP request.
    """
    logger = logging.getLogger(__name__ + ".get_request")
    request = None

    try:
        request = requests_retry_session(cbr.session).get(
            url,
            cookies=cookie,
            timeout=4
        )
        request.raise_for_status()
    except requests.exceptions.HTTPError as ex:
        logger.warning("An HTTP error occured.")
        logger.debug("HTTPError: {}.".format(ex))
        request = None
        time.sleep(cbr.cbr_config['crtimer'])
    except requests.exceptions.ConnectionError as ex:
        logger.warning("A Connection error occurred.")
        logger.debug("ConnectionError: {}.".format(ex))
        request = None
        time.sleep(cbr.cbr_config['crtimer'])
    except requests.exceptions.ConnectTimeout as ex:
        logger.warning("The request timed out while trying to connect to " +
                       "the remote server.")
        logger.debug("ConnectTimeout: {}.".format(ex))
        request = None
        time.sleep(60)
    except requests.exceptions.ReadTimeout as ex:
        logger.warning("The server did not send any data in the allotted " +
                       "amount of time.")
        logger.debug("ReadTimeout: {}.".format(ex))
        request = None
        time.sleep(60)
    except requests.exceptions.RequestException as ex:
        logger.exception("There was an ambiguous exception that occurred " +
                         "while handling your request.")
        raise SystemExit(1)

    return request


def post_request(cbr, url, data, headers, cookie={}):
    """Send a POST request wrapped in retries.

    Parameters:
        - cbr (CBRecord): The run session object.
        - url (str): URL for the Session object.
        - data (dict): Bytes, or file-like object to send in the body of the
          Request.
        - headers (dict): HTTP headers to add to the request.
        - cookie (CookieJar): A CookieJar containing all cookies to set on the
          session.

    Returns:
        - Response: The server’s response to the HTTP request.
    """
    logger = logging.getLogger(__name__ + ".post_request")
    request = None

    try:
        request = requests_retry_session(cbr.session).post(
            url,
            data=data,
            cookies=cookie,
            headers=headers,
            timeout=4
        )
        request.raise_for_status()
    except requests.exceptions.HTTPError as ex:
        logger.warning("An HTTP error occured.")
        logger.debug("HTTPError: {}.".format(ex))
        request = None
        time.sleep(cbr.cbr_config['crtimer'])
    except requests.exceptions.ConnectionError as ex:
        logger.warning("A Connection error occurred.")
        logger.debug("ConnectionError: {}.".format(ex))
        request = None
        time.sleep(cbr.cbr_config['crtimer'])
    except requests.exceptions.ConnectTimeout as ex:
        logger.warning("The request timed out while trying to connect to " +
                       "the remote server.")
        logger.debug("ConnectTimeout: {}.".format(ex))
        request = None
        time.sleep(60)
    except requests.exceptions.ReadTimeout as ex:
        logger.warning("The server did not send any data in the allotted " +
                       "amount of time.")
        logger.debug("ReadTimeout: {}.".format(ex))
        request = None
        time.sleep(60)
    except requests.exceptions.RequestException as ex:
        logger.exception("There was an ambiguous exception that occurred " +
                         "while handling your request.")
        raise SystemExit(1)

    return request
