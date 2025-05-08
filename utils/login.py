"""
This script is used to log in to the SJTU jAccount OAUTH2.0 authentication platform

Usage:
    from login import Login
    session = Login(clientURL, login_type)

Parameters:
    clientURL: str
        The URL of the client to be authorized.
    login_type: int | str
        The type of login. Default is 0. 
        0/'qrcode'/'qr' for QR code login.
        1/'password'/'pwd' for password login.
    cookies_path: os.PathLike
        The path to save the cookies. Default is 'cookies.json'.
    userinfo_path: os.PathLike
        The path to save the user info. Default is 'config.json'.
"""
import asyncio
import os.path
import json
import time
from urllib.parse import parse_qs, urlparse
from io import BytesIO

from requests.sessions import Session
from bs4 import BeautifulSoup
from qrcode import QRCode
from PIL import Image
import numpy as np

import websockets

################################################################################
# File IO
def load(filepath: os.PathLike) -> dict[str, str]:
    """
    Handle for loading JSON files.
    If the file does not exist, return an empty dictionary.
    """
    filepath = os.path.abspath(filepath)
    if not os.path.exists(filepath):
        return {}
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def save(content: dict[str, str], filepath: os.PathLike):
    """
    Handle for saving JSON files.
    This script will first load the file, then update the content and save it.
    """
    filepath = os.path.abspath(filepath)
    current_file = load(filepath)
    current_file.update(content)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(current_file, f, ensure_ascii=True, indent=4)

    print(f'Saved to {filepath}.')

################################################################################
# QR Code
def gen_qrcode(uuid, sig, ts):
    code = QRCode(border=1)
    uri = f"https://jaccount.sjtu.edu.cn/jaccount/confirmscancode?uuid={uuid}&ts={ts}&sig={sig}"
    code.add_data(uri)
    code.make()
    code.print_ascii(out=None, tty=False, invert=True)

def login_with_qrcode(uuid: str):
    """Login with QR code.
    This function will generate a QR code and wait for the user to scan it.
    After the user scans the QR code, the function will wait for the user to login.
    """
    url = f"wss://jaccount.sjtu.edu.cn/jaccount/sub/{uuid}"
    async def wss_client(url):
        async with websockets.connect(url) as websocket:
            await websocket.send('{"type": "UPDATE_QR_CODE"}')

            while True:
                # wait for response
                response = await websocket.recv()
                response = json.loads(response)
                if response['type'] == 'UPDATE_QR_CODE':
                    p = response['payload']
                    sig = p['sig']
                    ts = p['ts']
                    global img
                    img = gen_qrcode(uuid, sig, ts)
                elif response['type'] == 'LOGIN':
                    print("Login success!")
                    break

    asyncio.run(wss_client(url))

################################################################################
# User Info
def check_userinfo(username: str, password: str) -> tuple[str, str]:
    """
    Check if the username and password are empty.
    If empty, prompt the user to input them.
    """
    if not username:
        username = input("Please enter your username: ")
    if not password:
        password = input("Please enter your password: ")

    return username, password

def save_userinfo(username: str, password: str, path: os.PathLike):
    """
    Save the username and password to a file.
    Save condition is based on the user's input.
        If 'y', save both *username* and *password* to *path*.
        If 'n', remove the file if it exists.
        If 'u', save only *username* to *path* and remove the password.
    """
    print("Save your username and password? --- y: yes  n: no  u: username only")
    condition = input("(y/[n]/u): ").strip().lower() or "n"
    if condition == 'n':
        if os.path.exists(path):
            os.remove(path)
    else:
        if condition == 'y':
            content = {'username': username, 'password': password}
        elif condition == 'u':
            content = {'username': username, 'password': None}

        save(content, path)

################################################################################
# Captcha
def print_in_console(data):
        for row in data:
            print("".join(" " if x else "#" for x in row))

def remove_padding(data):
    row_cond = ~np.all(data == 1, axis=1)
    row_idx = np.where(row_cond)[0]
    if len(row_idx) > 0:
        data = data[row_idx[0]: row_idx[-1]+1, :]

    col_cond = ~np.all(data == 1, axis=0)
    col_idx = np.where(col_cond)[0]
    if len(col_idx) > 0:
        data = data[:, col_idx[0]: col_idx[-1]+1]

    return data

def print_captcha(image: Image):
    """Handle the captcha image and return the captcha string.
    """
    image = image.convert("L")
    data = np.array(image)
    data = (data - data.min()) / (data.max() - data.min())
    data = (data > 0.5).astype(int)
    data = remove_padding(data)
    print_in_console(data)
    return data

################################################################################
# Main Frame
class Login:
    """
    Login to the SJTU jAccount OAUTH2.0 authentication platform.

    Attributes
    ----------
    session : requests.Session
        The session object used to send requests and keep login state.

    Parameters
    ----------
    clientURL : str
        The URL of the client to be authorized.
    login_type : int | str
        The type of login. Default is 0.
        0/'qrcode'/'qr' for QR code login.
        1/'password'/'pwd' for password login.
    cookies_path : os.PathLike
        The path to save the cookies. Default is 'cookies.json'.
    userinfo_path : os.PathLike
        The path to save the user info. Default is 'config.json'.
    """
    def __init__(
            self,
            clientURL: str,
            login_type: int | str = 0,
            cookies_path: os.PathLike = 'cookies.json',
            userinfo_path: os.PathLike = 'config.json'
    ):
        self.clientURL = clientURL
        self.session = Session()
        self.session.headers = {
            "Accept-Language": "zh-CN",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Safari/605.1.15"
        }
        self.redit2auth(self.clientURL)

        if not self.login_with_cookies(cookies_path):
            self.session.cookies.pop("JAAuthCookie", None)  # Remove the expired cookies if exists

            if login_type in [0, 'qrcode', 'qr']:
                login_with_qrcode(self.uuid)
            elif login_type in [1, 'password', 'pwd']:
                self.login_with_pwd(userinfo_path)
            else:
                raise ValueError("Invalid loginType. Please use 0/qrcode/qr or 1/password/pwd.")
            
            print("Login success!\n")
            self.save_cookies(cookies_path)

    def redit2auth(self, clientURL: str):
        """Redirect to the authorization page and get the parameters."""
        res = self.session.get(clientURL)
        res.raise_for_status()
        self.auth_url = res.url

        if not self.auth_url.startswith("https://jaccount.sjtu.edu.cn/jaccount/jalogin"):
            raise Exception("Redirect to wrong page")
        
        self.auth_params = parse_qs(urlparse(res.url).query)
        soup = BeautifulSoup(res.text, 'html.parser')
        href: str = soup.find('a', attrs={'id': 'firefox_link'})['href']
        self.uuid = parse_qs(urlparse(href).query)['uuid'][0]

    def login_with_cookies(self, cookies_path: os.PathLike) -> bool:
        """Login with cookies saved in cookies.json."""
        print("Trying to login with cookies...\n")
        JAAuthCookie = load(cookies_path).get('JAAuthCookie', None)
        self.session.cookies.update({"JAAuthCookie": JAAuthCookie})        
        res = self.session.get(self.auth_url)
        res.raise_for_status()

        # Check login status
        if all([
            urlparse(res.url).netloc == 'jaccount.sjtu.edu.cn',
            urlparse(res.url).path == '/jaccount/jalogin'
        ]):
            print("Cookies expired. Please login Again.\n")
            return False
        else:
            print("Successfully login with cookies!\n")
            return True

    def save_cookies(self, cookies_path: os.PathLike):
        """Save JAAuthCookie."""
        cookies = self.session.cookies.get_dict()
        JAAuthCookie = cookies.get('JAAuthCookie', None)
        save({'JAAuthCookie': JAAuthCookie}, cookies_path)

    def login_with_pwd(self, userinfo_path: os.PathLike):
        userinfo = load(userinfo_path)
        username = userinfo.get('username', None)
        password = userinfo.get('password', None)

        while True:
            username, password = check_userinfo(username, password)
            save_userinfo(username, password, userinfo_path)

            while True:
                self.get_captcha()
                captcha = input("Please input the captcha: ")
                state = self.login_try(username, password, captcha)

                if state['errno'] == 0:
                    state = self.session.get("https://jaccount.sjtu.edu.cn" + state['url'])
                    state.raise_for_status()
                    return
                elif state['errno'] == 1:
                    if state['code'] == "WRONG_USER_OR_PASSWORD":
                        username, password = None, None
                        print(state['error'])
                        break
                    elif state['code'] == "WRONG_CAPTCHA":
                        print(state['error'])
                    else:
                        raise Exception(state['code'], state['error'])

    def get_captcha(self):
        """Get the captcha image."

        Returns:
        Image: The captcha image.
        """
        res = self.session.get(
            "https://jaccount.sjtu.edu.cn/jaccount/captcha",
            params={"uuid": self.uuid, "t": time.time_ns()//1000000},
            headers={"Referer": self.auth_url}
        )
        res.raise_for_status()
        image = Image.open(BytesIO(res.content))
        image = print_captcha(image)
        return image

    def login_try(self, username: str, password: str, captcha: str):
        login_url = "https://jaccount.sjtu.edu.cn/jaccount/ulogin"
        query ={
                "user": username,
                "pass": password,
                "uuid": self.uuid,
                "captcha": captcha,
                "lt": "p",
                **self.auth_params,
            }
        
        res = self.session.post(login_url, data=query, allow_redirects=False)
        res.raise_for_status()
        res = res.json()
        return res

if __name__ == "__main__":
    # Example usage
    login = Login('https://my.sjtu.edu.cn/login', login_type=1)
