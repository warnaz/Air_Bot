import asyncio
import json
import time
from dotenv import dotenv_values
from web3 import Web3
from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.signer.stark_curve_signer import KeyPair
from starknet_py.net.models import StarknetChainId, Invoke

env_vars = dotenv_values('.env')
wallet_address_two = env_vars['wallet_address_two']

# данные для MetaMask. Для Starknet по-другому нужно
test_wallet_address = wallet_address_two
test_private_key = env_vars['private_key']

wallet_address = Web3.to_checksum_address(test_wallet_address)
contract_address_usdt = Web3.to_checksum_address(wallet_address_two)

rpc = 'https://arb1.arbitrum.io/rpc'

eth_connect = Web3(Web3.HTTPProvider(endpoint_uri=rpc))


def read_abi():
    with open('abi.json', 'r') as f:
        abi = json.load(f)
    return abi


def get_gas_price():
    '''Gas price'''
    eth_gas_wei = eth_connect.eth.gas_price
    print(eth_gas_wei)

    return Web3.fromWei(eth_gas_wei, 'ether')


def get_balance_wallet():
    '''Balance'''
    check_sum = Web3.to_checksum_address(test_wallet_address)
    wallet_balance_wei = eth_connect.eth.get_balance(check_sum)
    wallet_balance = Web3.from_wei(wallet_balance_wei, 'ether')
    print(wallet_address)

    return wallet_balance


def address_from_key():
    ''' Смотрим, как из приватника вывести адрес кошелька '''
    address_from_key = eth_connect.eth.account.from_key(private_key=test_private_key).address 
    print(address_from_key)

    return address_from_key


def work_with_contract():
    abi = read_abi()

    contract = eth_connect.eth.contract(
        address=contract_address_usdt,
        abi=abi)
    balance_of = contract.functions.balanceOf(wallet_address).call()
    print(balance_of)
    
    return balance_of

