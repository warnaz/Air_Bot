import asyncio
from web3 import Web3
from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.signer.stark_curve_signer import KeyPair
from starknet_py.net.models import StarknetChainId, Invoke
from PROJECTS.STARKNET.route import main
from dotenv import dotenv_values

config = dotenv_values(".env")
test_private_key_one = config['test_private_key_one']
wallet_address_one = config['wallet_address_one']

# Данные для Starknet
WALLET_ADDRESS = wallet_address_one
PRIVATE_KEY = test_private_key_one

rpc = 'https://starknet-mainnet.public.blastapi.io'

key_pair = KeyPair.from_private_key(PRIVATE_KEY)
client = FullNodeClient(rpc)
account = Account(
            address=WALLET_ADDRESS,
            client=client,
            key_pair=key_pair,
            chain=StarknetChainId.MAINNET,
        )

async def get_balance():
    balance_wei = await account.get_balance()
    balance = Web3.from_wei(balance_wei, 'ether')
    print(balance)

asyncio.run(get_balance())
