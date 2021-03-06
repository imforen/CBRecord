"""Fetches data from the website.

Fuctions:
    - make_request: Fetch HTML from the given url.
    - is_logged_in: Check if the user is logged in to CB.
    - login: Try to log in to CB.
    - get_models: Get a list of online followed models who are free to watch.
"""

import json
import os
import requests
import time

from base64 import b64decode
from bs4 import BeautifulSoup

from cbrecord import const
from cbrecord.util import log


def make_request(url, cbr, initial_login=False):
    """Fetch HTML from the given url.

    Parameters:
        - url (string): The url to get HTML from.
        - cbr (object): The run session object (CBRecord class).
        - initial_login (bool): True if first login attempt.

    Returns:
        - string: The HTML code requested from the given url.
    """
    request = None
    cookie = {}
    already_logged_in = True

    try:
        if os.path.isfile(const.CONFIG_DIR + const.COOKIE_FN):
            with open(const.CONFIG_DIR + const.COOKIE_FN, 'r') as f:
                cookie = requests.utils.cookiejar_from_dict(json.load(f))
    except json.JSONDecodeError:
        log("Cookie file error", cbr, 30)

    while request is None:
        try:
            request = cbr.session.get(url, timeout=10, cookies=cookie)
            request.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            log("An HTTP error occured", cbr, 30)
            log("Error message: ", cbr, 10, ex)
            print("Retrying in 10 minutes.")
            request = None
            time.sleep(600)
        except requests.exceptions.ConnectionError as ex:
            log("No internet connection", cbr, 30)
            log("Error message: ", cbr, 10, ex)
            print("Retrying in 10 minutes.")
            request = None
            time.sleep(600)
        except requests.exceptions.Timeout as ex:
            log("Connection timeout", cbr, 30)
            log("Error message: ", cbr, 10, ex)
            print("Retrying in 10 minutes.")
            request = None
            time.sleep(600)
        except requests.exceptions.TooManyRedirects as ex:
            log("Too many redirects", cbr, 40)
            log("Error message: ", cbr, 10, ex)
            raise SystemExit(1)
        except requests.exceptions.RequestException as ex:
            log("An unexpected HTTP request error occured", 40, "", cbr)
            log("Error message: ", 10, ex, cbr)
            raise SystemExit(1)

        while (request is not None) and (is_logged_in(request.text) is False):
            already_logged_in = False
            login(cbr)
            request = cbr.session.get(url, timeout=4, cookies=cookie)

    if (already_logged_in is True) and (initial_login is True):
        log("Already logged in", cbr, 20)
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
    url = b64decode(b'aHR0cHM6Ly9jaGF0dXJiYXRlLmNvbS' +
                    b'9hdXRoL2xvZ2luLz9uZXh0PS8=').decode("utf-8")
    result = cbr.session.get(url)
    soup = BeautifulSoup(result.text, 'html.parser')
    csrf = soup.find('input', {'name': 'csrfmiddlewaretoken'}).get('value')
    agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36' \
            '(KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'

    result = cbr.session.post(url,
                              data={
                                  'csrfmiddlewaretoken': csrf,
                                  'username': cbr.cbr_config['username'],
                                  'password': cbr.cbr_config['password'],
                                  'rememberme': 'on',
                                  'next': '/',
                              },
                              cookies=result.cookies,
                              headers={
                                  'user-agent': agent,
                                  'Referer': url
                              })

    if is_logged_in(result.text) is True:
        with open(const.CONFIG_DIR + const.COOKIE_FN, 'w+') as f:
            json.dump(requests.utils.dict_from_cookiejar(result.cookies), f)
        log("Login successful as: ", cbr, 20, cbr.cbr_config['username'])
    else:
        log("Login failed to: ", cbr, 30, cbr.cbr_config['username'])
        print("Wrong user credentials or too many login attempts.")
        raise SystemExit(0)


def get_models(cbr):
    """Get a list of online followed models who are free to watch.

    Parameters:
        - cbr (object): The run session object (CBRecord class).

    Returns:
        - list: A list of online followed models who are free to watch.
    """
    url = b64decode(b'aHR0cHM6Ly9jaGF0dXJiYXR' +
                    b'lLmNvbS9mb2xsb3dlZC1jYW1zLw==').decode("utf-8")
    html = make_request(url, cbr)
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
        log("No followed models error", cbr, 40)
        raise SystemExit(1)

    return models
