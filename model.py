import base64

import aiohttp
from web3 import Account
from eth_account.messages import encode_defunct

from file_manager import FileManager
from utils import log, get_current_time

from proxy_rotator import rotator


class ProxyClientSession(aiohttp.ClientSession):
    def __init__(self, proxy: str, proxy_auth: aiohttp.BasicAuth, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._default_proxy = proxy
        self._default_proxy_auth = proxy_auth

    async def _request(self, method, url, **kwargs):
        if 'proxy' not in kwargs:
            kwargs['proxy'] = self._default_proxy
        if 'proxy_auth' not in kwargs:
            kwargs['proxy_auth'] = self._default_proxy_auth
        return await super()._request(method, url, **kwargs)

    def __del__(self):
        pass


class TSBAccount:
    def __init__(self, private_key: str, results_writer: FileManager, unbanned_writer: FileManager):
        self.private_key = private_key
        self.erc_address: str | None = None
        self.sandbox_ID: str | None = None
        self.sandbox_username: str | None = None
        self.sandbox_banned: bool | None = None
        self.proxy: str = ""
        self.headers: dict = {}
        self.useragent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
        self.session: ProxyClientSession | None = None
        self.token: str = ""
        self.results_writer: FileManager | None = results_writer
        self.unbanned_writer: FileManager | None = unbanned_writer

        self._setup_session()

    @staticmethod
    def _setup_proxy() -> tuple[str, aiohttp.BasicAuth]:
        proxy_data = rotator.get_next_proxy()
        ip, port, username, password = proxy_data.split(":")
        proxy_auth = aiohttp.BasicAuth(username, password)
        proxy_url = f"http://{ip}:{port}"
        return proxy_url, proxy_auth

    def _setup_headers(self):
        """
        Для того, чтоб получить правильные Headersы, нужно разобраться с механизмом авторизации
        В TSB используется Base64, однако есть некие хитрости с подписью, и использованием двоеточия после адреса
        """

        erc_address = Account.from_key(self.private_key).address
        self.erc_address = erc_address
        encoded_erc_address = base64.b64encode(f"{self.erc_address}:".encode()).decode()

        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            "authorization": f"Basic {encoded_erc_address}",
            'cache': 'no-cache',
            'origin': 'https://www.sandbox.game',
            'priority': 'u=1, i',
            'referer': 'https://www.sandbox.game/',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': self.useragent,
            'x-csrf-token': '',
        }

    def _setup_session(self):
        # Разбираемся с прокси
        proxy_url, proxy_auth = self._setup_proxy()

        # Устанавливаем необходимые хедерсы
        self._setup_headers()

        # Создаем кастомную сессию
        self.session = ProxyClientSession(proxy_url, proxy_auth, headers=self.headers)

    async def _get_token(self) -> str:
        async with self.session.post("https://api.sandbox.game/auth/login/builtin/request") as response:
            challenge = await response.text()

            if response.cookies.get("tsb_www_challenge") is not None:
                tsb_www_challenge = response.cookies.get("tsb_www_challenge").value
            else:
                return ""

        msg = f"Welcome to The Sandbox Dashboard, please sign this message to verify your identity. Your custom challenge is: {challenge}"
        msg_hash = encode_defunct(text=msg)
        signature = Account.sign_message(msg_hash, self.private_key).signature.hex()
        b64signature = base64.b64encode(
            f"{self.erc_address}:0x{signature}".encode()
        ).decode()
        self.session.headers["authorization"] = f"Basic {b64signature}"

        json_challenge_data = {"challenge": challenge, "type": "builtin"}
        cookies = {"tsb_www_challenge": tsb_www_challenge}

        async with self.session.post("https://api.sandbox.game/auth/login/builtin/verify",
                                     cookies=cookies,
                                     json=json_challenge_data) as response:
            if response.cookies.get("tsb_www_token") is None:
                return ""

            self.token = response.cookies["tsb_www_token"].value

        return self.token

    async def _ping_sandbox(self) -> str:
        async with self.session.get("https://api.sandbox.game/auth/isLoggedIn") as response:
            ping_response_data = await response.json()

            tsb_username = ping_response_data.get("username")
            tsb_id = ping_response_data.get("id")
            if tsb_username is None or tsb_id is None:
                return "NOT_AUTHENTICATED"

            self.sandbox_ID = tsb_id
            self.sandbox_username = f"..{tsb_username[-6:]}"

            return tsb_username

    async def login(self) -> bool:
        log(f"Logging into {self.private_key[:12]}...")
        await self._get_token()
        if self.token is not None:
            tsb_username = await self._ping_sandbox()

            if tsb_username == "NOT_AUTHENTICATED":
                log(f"Failed to login into TSB with {self.private_key[:12]}.")
                return False

            log(f"Successfully logged for {self.private_key[:12]}: {tsb_username}.")
            return True

    async def close_session(self):
        if self.session is not None:
            await self.session.close()

    async def get_inventory(self):
        log(f"Checking claims-inventory for {self.private_key[:12]}: {self.sandbox_username}.")
        params = {
            'userId': self.sandbox_ID,
            'onlyUnclaimed': 'true',
            'includeGiveaway': 'true',
            'includeBlockchainData': 'true',
        }

        inv_items_names = []
        claim_empty = True
        search_empty = True

        total_inv_length = 0

        async with self.session.get("https://api.sandbox.game/instant-giveaways/claim", params=params) as response:
            inventory_response_data = await response.json()
            # print(inventory_response_data)
            if inventory_response_data.get("denied") is True:
                log(f"TSB: {self.sandbox_username}, PKEY: {self.private_key[:12]} is banned. (Claims inventory)")
                self.sandbox_banned = True
            else:
                self.sandbox_banned = False

                inv_response_items = inventory_response_data.get("rows")
                if inv_response_items:
                    claim_empty = False
                    for item in inv_response_items:
                        item: dict
                        total_inv_length += 1
                        title = item.get('title')
                        name = item.get('name')
                        valid_name = title or name
                        if valid_name:
                            inv_items_names.append(valid_name)

        log(f"Checking search-inventory for {self.private_key[:12]}: {self.sandbox_username}.")
        async with self.session.get(
                f"https://api.sandbox.game/assetclaims/search?userId={self.sandbox_ID}") as response:
            search_inventory_response_data = await response.json()

            if len(search_inventory_response_data) > 0:
                search_empty = False
                for item in search_inventory_response_data:
                    item: dict
                    total_inv_length += 1
                    title = item.get('title')
                    name = item.get('name')
                    valid_name = title or name
                    if valid_name:
                        inv_items_names.append(valid_name)

        if inv_items_names:
            log(f"Found items in inventory. TSB: {self.sandbox_username}, PKEY: {self.private_key[:12]}, items: {inv_items_names}")
        elif not claim_empty or not search_empty:
            log(f"Found smth in inventory. TSB: {self.sandbox_username}, PKEY: {self.private_key[:12]}")


        res_data = f"{self.private_key} | {self.sandbox_username} | banned={self.sandbox_banned} | items_amount={total_inv_length} | {get_current_time()}"
        self.results_writer.write_line(res_data)
        if not self.sandbox_banned:
            self.unbanned_writer.write_line(res_data)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()
