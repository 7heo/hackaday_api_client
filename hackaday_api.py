#!/usr/bin/env python3
"HackADay API client"

# This script is a work in progress, I've replaced a few simple calls with more
# complex ones, for debugging purposes (like the VerboseRequest class instead
# of simple calls to requests, or the use of webbrowser instead of requests
# too).
#
# The point is that, as is, with the account I had for testing, the API /token
# endpoint returns 403 anyway. I cannot get any information as to why, and the
# hackaday team isn't responsive. So, for now, this is shelved. ¯\_(ツ)_/¯

from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from json import load as json_load
from os.path import expanduser
from threading import Thread
from types import SimpleNamespace
from urllib.parse import parse_qs
from urllib.parse import urlencode
from urllib.parse import urlsplit
from urllib.parse import urlunsplit
from webbrowser import open as webbrowser_open

from requests import Session as requests_Session
# from requests import post as requests_post
from requests_toolbelt.utils import dump  # type: ignore [import-untyped]

OAUTH_INFO_FILE = "~/.hackaday_api.json"  # JSON data with client_id, etc.
CODE_FILE = "~/.hackaday_api_code"  # API Code returned by /authenticate


class VerboseRequest(requests_Session):
    "Make requests verbose"
    def send(self, request, **kwargs):
        prefixes = dump.PrefixSettings(b'< ', b'> ')

        data = bytearray()

        try:
            dump._dump_request_data(request, prefixes, data)  # pylint: disable=protected-access # noqa: E501
            resp = super().send(request, **kwargs)
            dump._dump_response_data(resp, prefixes, data)  # pylint: disable=protected-access # noqa: E501
        finally:
            print(data.decode('utf-8'))

        return resp


class OAuthFlowHandler(BaseHTTPRequestHandler):
    "Simple OAuth flow handler"

    def _register_code_with_server_class(self, data):
        self.server.last_request = SimpleNamespace()
        self.server.last_request.query = data

    def _send_successful_auth_message(self):
        self._send_response('<p>Authentication successful. You can now close '
                            'this browser tab.</p>')

    def _serve_welcome_page(self):
        uri = get_auth_uri_2(self.server.client_id, self.server.call_back_url)
        self._send_response(f'<p>Could not obtain a valid OAuth code.</p>'
                            f'<p><a href="{uri}">Click here to authenticate'
                            '</a>.</p>')

    def _serve_form(self):
        with open(expanduser(OAUTH_INFO_FILE), 'r', encoding='UTF-8') as _fh:
            data = json_load(_fh)
        self._send_response('<form action="https://hackaday.io/token" '
                            'method="POST">'
                            '<input style="width: 100%" type="text"'
                            'name="client_id" '
                            f'value="{data["client_id"]}">'
                            '<br><input style="width: 100%" type="text" '
                            'name="client_secret" '
                            f'value="{data["client_secret"]}"><br>'
                            '<input style="width: 100%" type="text" '
                            'name="code" '
                            f'value="{self.server.data["code"]}"><br>'
                            '<input style="width: 100%" type="text" '
                            'name="code" '
                            f'value="{self.server.data["scope"]}"><br>'
                            '<input style="width: 100%" type="text" disabled '
                            'name="scope" '
                            'value="authorization_code"><br>'
                            '<input style="width: 100%" type="text" disabled '
                            'name="redirect_uri" '
                            f'value="{data["call_back_url"]}"><br>'
                            '<input type="submit" value="Submit">'
                            '</form>')

    def _send_response(self, response: str, code=200):
        self.__class__.server_version = "OauthHandler/0.1"
        # self.sys_version = "Python/3.13.5"
        self.send_response(code)
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
        # self.wfile.flush()
        # self.finish()

    def do_GET(self):  # pylint: disable=invalid-name
        "HTTP do_GET"
        data = parse_qs(urlsplit(self.path).query)
        if isinstance(data, dict) and len(data):
            data = {x: ''.join(y) for x, y in data.items()}
            self._register_code_with_server_class(data)
            self._send_successful_auth_message()
            server_thread = Thread(target=self.server.shutdown)
            server_thread.daemon = True
            server_thread.start()
        else:
            if self.path == '/form':
                self._serve_form()
            else:
                self._serve_welcome_page()

    def log_message(self, format, *args):  # pylint: disable=redefined-builtin
        "Logs a message"


def get_auth_uri_1(client_id, call_back_url):
    """Get URI"""
    return f"https://hackaday.io/authorize?client_id={client_id}&redirect_uri"\
           f"={call_back_url}&response_type=code&scope=private-apis:read"


def get_auth_uri_2(client_id, call_back_url):
    """Get URI"""
    return urlunsplit(('https', 'hackaday.io', 'authorize',
                       urlencode({'client_id': client_id,
                                  'redirect_uri': call_back_url,
                                  'response_type': 'code',
                                  'scope': 'private-apis:read'}), ''))


def perform_oauth():
    "Perform OAuth"
    with open(expanduser(OAUTH_INFO_FILE), 'r', encoding='UTF-8') as _fh:
        data = json_load(_fh)
    info = urlsplit(data['call_back_url'])
    srv = HTTPServer((info.hostname, int(info.port)), OAuthFlowHandler)
    srv.client_id = data['client_id']
    srv.call_back_url = data['call_back_url']
    webbrowser_open(data['call_back_url'])
    print(f"Open {data['call_back_url']} to authenticate")
    srv.serve_forever()
    srv.data = srv.last_request.query  # pylint: disable=no-member
    server_thread = Thread(target=srv.handle_request)
    server_thread.daemon = True
    server_thread.start()
    return srv.last_request.query['code']  # pylint: disable=no-member


def get_token(code: str) -> str:
    "Get auth token from OAuth code"
    url = 'https://hackaday.io/token'
    with open(expanduser(OAUTH_INFO_FILE), 'r', encoding='UTF-8') as _fh:
        data = json_load(_fh)
    params = {
            'client_id': data['client_id'],
            'client_secret': data['client_secret'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': data['call_back_url'],
    }
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:140.0) '
                             'Gecko/20100101 Firefox/140.0'}
    # 'Content-Type': 'application/x-www-form-urlencoded'}

    # Manual debug, to see in the browser what is happening
    webbrowser_open("http://localhost:8080/form")

    _ = (url, params, headers)

    # Disabled for manual debug
    # x = requests_post(url, headers=headers, data=params, timeout=10)
    # x = VerboseRequest().post(url, headers=headers, data=params, timeout=10)
    # if int(x.status_code) != 200:
    #     raise RuntimeError(f"Got HTTP code {x.status_code} from OAuth token "
    #                        "request.")
    # return x.text
    return ''


def main():
    "Main"
    code = None
    try:
        with open(expanduser(CODE_FILE), 'r', encoding='UTF-8') as _fh:
            code = _fh.read()
    except FileNotFoundError:
        pass
    if not code:
        code = perform_oauth()
    access_token = get_token(code)
    print("You can now close (^C) the script when you are done in the browser")
    input("")
    print(access_token)


if __name__ == "__main__":
    main()
