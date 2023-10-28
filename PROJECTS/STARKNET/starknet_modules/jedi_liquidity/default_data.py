from decimal import Decimal
from random import choice, uniform
from typing import Union
from loguru import logger
from dataclasses import dataclass
from starknet_modules.jedi_liquidity.path import *
import json
from starknet_modules.starknet import Starknet
from config import *


class TokenAmount:
    Wei: int
    Ether: Decimal
    decimals: int

    def __init__(self, amount: Union[int, float, str, Decimal], decimals: int = 18, wei: bool = False) -> None:
        if wei:
            self.Wei: int = amount
            self.Ether: Decimal = Decimal(str(amount)) / 10 ** decimals

        else:
            self.Wei: int = int(Decimal(str(amount)) * 10 ** decimals)
            self.Ether: Decimal = Decimal(str(amount))

        self.decimals = decimals


@dataclass
class DefaultContractData:
    TOKEN_ADDRESSES = {
        'ETH': {
            'name': 'ETH',
            'address': 0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7,
            'abi': json.load(open(ETH_ABI_PATH)),
            'decimals': 18
        },
        'USDT': {
            'name': 'USDT',
            'address': 0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8,
            'abi': json.load(open(USDT_ABI_PATH)),
            'decimals': 6
        },
        'USDC': {
            'name': 'USDC',
            'address': 0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8,
            'abi': json.load(open(USDC_ABI_PATH)),
            'decimals': 6
        },
        'DAI': {
            'name': 'DAI',
            'address': 0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3,
            'abi': json.load(open(DAI_ABI_PATH)),
            'decimals': 18
        }
    }

    JEDISWAP_ADDRESSES = {
        'ETHUSDC': {
            'name': 'ETHUSDC',
            'address': 0x04d0390b777b424e43839cd1e744799f3de6c176c7e32c1812a41dbd9c19db6a,
            'abi': json.load(open(JEDISWAP_ETHUSDC_ABI_PATH)),
            'decimals': 18
        },
        'ETHUSDT': {
            'name': 'ETHUSDT',
            'address': 0x045e7131d776dddc137e30bdd490b431c7144677e97bf9369f629ed8d3fb7dd6,
            'abi': json.load(open(JEDISWAP_ETHUSDT_ABI_PATH)),
            'decimals': 18
        },
        'USDCUSDT': {
            'name': 'USDCUSDT',
            'address': 0x05801bdad32f343035fb242e98d1e9371ae85bc1543962fedea16c59b35bd19b,
            'abi': json.load(open(JEDISWAP_USDCUSDT_ABI_PATH)),
            'decimals': 18
        },
        'DAIUSDT': {
            'name': 'DAIUSDT',
            'address': 0x00f0f5b3eed258344152e1f17baf84a2e1b621cd754b625bec169e8595aea767,
            'abi': json.load(open(JEDISWAP_DAIUSDT_ABI_PATH)),
            'decimals': 18
        },
        'DAIUSDC': {
            'name': 'DAIUSDC',
            'address': 0x00cfd39f5244f7b617418c018204a8a9f9a7f72e71f0ef38f968eeb2a9ca302b,
            'abi': json.load(open(JEDISWAP_DAIUSDC_ABI_PATH)),
            'decimals': 18
        },
        'DAIETH': {
            'name': 'DAIETH',
            'abi': json.load(open(JEDISWAP_DAIETH_ABI_PATH)),
            'address': 0x07e2a13b40fc1119ec55e0bcf9428eedaa581ab3c924561ad4e955f95da63138,
            'decimals': 18
        }
    }

    REVERSE_JEDISWAP_ADDRESSES = {
        'USDCETH': 'ETHUSDC',
        'USDCDAI': 'DAIUSDC',
        
        'USDTETH': 'ETHUSDT',
        'USDTDAI': 'DAIUSDT',
        'USDTUSDC': 'USDCUSDT',

        'ETHDAI': 'DAIETH'
    }

    JEDISWAP_CONTRACT = {'address': 0x041fd22b238fa21cfcf5dd45a8548974d8263b3a531a60388411c5e230f97023,
                         'abi': json.load(open(JEDISWAP_ABI_PATH))}

    @staticmethod
    def get_data_from_contract(token_name) -> dict:

        reverse = False

        if contract := DefaultContractData.TOKEN_ADDRESSES.get(token_name):
            return contract, reverse
        elif contract := DefaultContractData.JEDISWAP_ADDRESSES.get(token_name):
            return contract, reverse
        elif contract := DefaultContractData.REVERSE_JEDISWAP_ADDRESSES.get(token_name):
            reverse = True
            return DefaultContractData.JEDISWAP_ADDRESSES.get(contract), reverse
        else:
            raise ValueError(f"Contract {token_name} not found")

async def _get_data_for_liquidity_pool(client, dex_name: str, data: dict) -> dict:
    try:
        from_token = data.get('from_token')
        to_token = data.get('to_token')
        
        token_one_name = from_token
        token_two_name = to_token

        token_one_data, reverse = DefaultContractData.get_data_from_contract(from_token)
        token_two_data, reverse = DefaultContractData.get_data_from_contract(to_token)

        token_one_address = token_one_data.get('address')
        token_two_address = token_two_data.get('address')

        token_one_decimals = token_one_data.get('decimals')
        token_two_decimals = token_two_data.get('decimals')

        pooled_token_data = {}
        amount_one = data.get('amount_one')
        amount_two = data.get('amount_two')
        amount_in_usdt = 0

        pooled_token_data, reverse = DefaultContractData.get_data_from_contract(from_token + to_token)
        pooled_token_address = pooled_token_data.get('address')
        pooled_token_name = pooled_token_data.get('name')
        
        if reverse:
            amount_one, amount_two = amount_two, amount_one
            token_one_address, token_two_address = token_two_address, token_one_address
            token_one_decimals, token_two_decimals = token_two_decimals, token_one_decimals
            token_one_name, token_two_name = token_two_name, token_one_name

        balanceOf_first = await client.get_balance(token_address=token_one_address, decimals=token_one_decimals)
        balanceOf_second = await client.get_balance(token_address=token_two_address, decimals=token_two_decimals)

        if balanceOf_second.Wei <= 0 or balanceOf_first.Wei <= 0:
            return {}
    
        if amount_one and amount_two:
            return {'pooled_token_address': pooled_token_address,
                    'pooled_token_name': pooled_token_name,
                    'amount_one': amount_one,
                    'amount_two': amount_two,
                    'amount_in_usdt': amount_in_usdt,
                    'token_one_address': token_one_address,
                    'token_two_address': token_two_address,
                    'token_one_name': token_one_name,
                    'token_two_name': token_two_name,
                    'token_one_decimals': token_one_decimals,
                    'token_two_decimals': token_two_decimals}
    except Exception as exc:
        logger.error(f"[{client.address}] Couldn't get data for adding liquidity | {exc}")


async def get_data_for_liquidity_pool(client: Starknet, dex_name: str, data: dict):
    for _ in range(15):
        data = await _get_data_for_liquidity_pool(client=client, dex_name=dex_name, data=data)
        if data != {}:
            return data
