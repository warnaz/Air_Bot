import random
import sys
import questionary
import uvicorn

from questionary import Choice
from fastapi import FastAPI
from typing import List, Union
from pydantic import BaseModel

from config import RECIPIENTS
from utils.sleeping import sleep
from modules_settings import *
from settings import TYPE_WALLET, RANDOM_WALLET, IS_SLEEP, SLEEP_FROM, SLEEP_TO
from models import CRUD
from route import Route
from constants import StarknetActions

def get_module(name, wallet):

    result = questionary.select(
        "Select a method to get started",
        choices=[
            # Choice("1) Make deposit to Starknet", deposit_starknet),
            # Choice("2) Make withdraw from Starknet", withdraw_starknet),
            # Choice("3) Bridge on Orbiter", bridge_orbiter),
            Choice("1) Make swap on JediSwap", swap_jediswap),
            Choice("2) Make swap on MySwap", swap_myswap),
            Choice("3) Make swap on 10kSwap", swap_starkswap),
            Choice("4) Make swap on SithSwap", swap_sithswap),
            Choice("5) Make swap on Avnu", swap_avnu),
            Choice("6) Make swap on Protoss", swap_protoss),
            Choice("7) Mint Starknet ID", mint_starknet_id),
            Choice("8) Dmail send mail", send_mail_dmail),
            Choice("9) JediSwap add liquidity", add_liquidity_jediswap),
            # Choice("9) Mint NFT on Pyramid", create_collection_pyramid),
            Choice("10) Check transaction count", "tx_checker"),
            Choice("11) Exit", "exit"),

            # Choice("10) Make swap on Fibrous", swap_fibrous),
            # Choice("11) Deposit ZkLend", deposit_zklend),
            # Choice("12) Withdraw ZkLend", withdraw_zklend),
            # Choice("13) Enable collateral ZkLend", enable_collateral_zklend),
            # Choice("14) Disable collateral ZkLend", disable_collateral_zklend),
            # Choice("17) Mint StarkVerse NFT", mint_starkverse),
            # Choice("19) Transfer", make_transfer),
            # Choice("20) Swap tokens to ETH", swap_tokens),
            # Choice("21) Use Multiswap", swap_multiswap),
            # Choice("22) Use custom routes ", custom_routes),
        ],
        qmark="⚙️ ",
        pointer="✅ "
    ).ask()
    if result == "exit":
        sys.exit()


def get_wallets(private_key: str, use_recipients: bool = False) -> List[dict]:
    """ Получаем список из приватных ключей клиента """

    _ACCOUNTS = [private_key]

    if use_recipients:
        account_with_recipients = dict(zip(_ACCOUNTS, RECIPIENTS))

        wallets = [
            {
                "id": _id,
                "key": key,
                "recipient": account_with_recipients[key],
            } for _id, key in enumerate(account_with_recipients, start=1)
        ]
    else:
        wallets = [
            {
                "id": _id,
                "key": key,
            } for _id, key in enumerate(_ACCOUNTS, start=1)
        ]

    return wallets


def run_module(module, data, account_id, key, recipient: Union[str, None] = None):
    if recipient:
        asyncio.run(module(account_id, key, TYPE_WALLET, recipient, data))
    else:
        asyncio.run(module(account_id, key, TYPE_WALLET, data=data))


def main(module, data):
    private_key = data.get("private_key")

    if module in [deposit_starknet, withdraw_starknet, bridge_orbiter, make_transfer]:
        wallets = get_wallets(private_key=private_key, use_recipients=True)
    else:
        wallets = get_wallets(private_key=private_key)

    if RANDOM_WALLET:
        random.shuffle(wallets)

    for account in wallets:
        run_module(module, data, account.get("id"), account.get("key"), account.get("recipient", None))

        if account != wallets[-1] and IS_SLEEP:
            sleep(SLEEP_FROM, SLEEP_TO)


if __name__ == '__main__':

    app = FastAPI()

    class RequestData(BaseModel):
        data: dict

    @app.post("/")
    def root(request_data: RequestData):
        data = request_data.data
        route_id = data.get('route_id')

        crud = CRUD()
        route = Route(route_id, crud)
        project = crud.get_project()
        action_list = route.actions
        client, wallet = asyncio.run(crud.create_client_wallet(data))

        for item in action_list:

            try:
                action = asyncio.run(crud.get_single_action(route_id, item.id))

                asyncio.run(crud.create_action_wallet(
                    wallet=wallet, 
                    action=action, 
                    status="IN_PROGRESS"
                    )
                )
                module = swap_protoss
                main(module=module, data=data)
            except Exception as e:
                asyncio.run(crud.create_status(
                    code=500,
                    desc=str(e),
                    client=client,
                    wallet=wallet,
                    project=1,
                    route=route,
                    action=action                    
                )
            )

        return {"[STATUS]": "SUCCESS"}

    uvicorn.run(app, host="localhost", port=8001)
