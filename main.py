import asyncio

import warnings
warnings.filterwarnings("ignore", message="Unclosed client session")

from file_manager import results_manager, unbanned_manager
from model import TSBAccount
from utils import log, get_current_time

input_data = []
total_pkeys = 0
total_proxies = 0

def initialization():
    global input_data
    global total_pkeys
    global total_proxies

    with open("privatekeys.txt", "r") as pkeys_file:
        input_data = [line.strip().removeprefix("0x") for line in pkeys_file.readlines()]
        if len(input_data) == 0:
            raise Exception("No private keys found. Insert privatekeys into \"privatekeys.txt\" file.")

        total_pkeys = len(input_data)

    with open("proxies.txt", "r") as proxies_file:
        proxies = [line.strip() for line in proxies_file.readlines()]
        if len(proxies) == 0:
            raise Exception("No proxies found. Insert proxies into \"proxies.txt\" file (ip:port:login:password).")

        for line in proxies:
            if len(line.split(":")) != 4:
                raise Exception(f"Bad proxies. Every string should be in IP:PORT:USER:PASSWORD format. Crashed at: {line}")

        total_proxies = len(proxies)


async def process_account(private_key: str):
    account = TSBAccount(private_key, results_manager, unbanned_manager)
    try:
        await account.login()
        await account.get_inventory()
        await account.close_session()
    except Exception as e:
        log(f"Error {e.__class__.__name__}: {e}, while checking {private_key}")
        results_manager.write_line(f"{private_key} | ERROR | ERROR | ERROR | {get_current_time()}")
        await account.close_session()

async def main():
    tasks = []
    delay = 60 / (3 * total_proxies)
    log(f"Your delay: {delay}. Add more proxies, to minimize it.")
    n = len(input_data)
    for i, private_key in enumerate(input_data):
        tasks.append(asyncio.create_task(process_account(private_key)))
        if i != n - 1:
            await asyncio.sleep(delay)
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    initialization()
    log(f"TSB fast-checker V1.0.0 started. Accounts loaded: {total_pkeys}, proxies amount: {total_proxies}")
    asyncio.run(main())
    log("Successfully checked.")