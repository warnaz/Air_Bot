import asyncio
# from decimal import Decimal
import random

import requests

from loguru import logger
# from web3 import Web3
# from src.config import NODE_URL, MAX_GWEI, RANDOM_INCREASE_FEE, USE_PROXY, DELAY_BETWEEN_ACTIONS, CURRENT_ACCOUNTS_CAIRO_VERSION
# from src.models.models import TokenAmount, DefaultContractData
# from src.utils.utils import PROXY_ITER
# from src.logger import logger
from typing import Optional
# from starknet_py.net.account.account import Account
# from starknet_py.net.full_node_client import FullNodeClient
# from starknet_py.net.models import StarknetChainId
# from starknet_py.net.signer.stark_curve_signer import KeyPair, StarkCurveSigner
from starknet_py.contract import Contract
# from aiohttp import ClientSession
# from aiohttp_socks import ProxyConnector
# from starknet_py.net.gateway_client import GatewayClient

from utils.gas_checker import check_gas
from starknet_modules.starknet import Starknet
from config import CURRENT_ACCOUNTS_CAIRO_VERSION
from starknet_modules.jedi_liquidity.default_data import DefaultContractData, TokenAmount


class Client(Starknet):

    async def _approve(self, token_name, token_data, spender, amount) -> bool:
        abi = token_data.get('abi')
        token_address = token_data.get('address')
        logger.debug(f"[{self.address}] Approving {token_name}...")
        contract = Contract(address=token_address, abi=abi,
                            provider=self.account)
        call_data = [contract.functions['approve'].prepare(spender=spender,
                                                           amount=amount)]
        tx = await self.call(call_data=call_data)
        if tx:
            return True


    async def get_balance(self, token_address=0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7,
                          decimals=18) -> TokenAmount:
        balance = await self.account.get_balance(token_address=token_address)
        return TokenAmount(amount=balance, wei=True, decimals=decimals)


    async def approve_interface(
            self,
            token_name,
            spender,
            decimals,
            amount: Optional[TokenAmount] = None
        ) -> bool:
        token_data, reverse = DefaultContractData.get_data_from_contract(token_name=token_name)
        token_address = token_data.get('address')
        balance = await self.get_balance(token_address=token_address, decimals=decimals)
        if balance.Wei <= 0:
            logger.error(f"[{self.address}] Zero balance for {token_name}")
            return False
        if not amount or amount.Wei > balance.Wei:
            amount = balance
        approved_amount = await self.get_allowance(token_data=token_data, spender=spender)
        if approved_amount.Wei >= amount.Wei:
            logger.debug(f"[{self.address}] Already approved {approved_amount.Ether} {token_name}")
            return True

        approved_tx = await self._approve(
            token_name=token_name,
            token_data=token_data,
            amount=amount.Wei,
            spender=spender
        )
        if approved_tx:
            logger.debug(f"[{self.address}] Approved {amount.Ether} {token_name}")
            random_sleep = random.randint(30, 40)
            logger.info(f"[{self.address}] Sleeping for {random_sleep} sec g tx...")
            await asyncio.sleep(random_sleep)
            return True
        return False


    async def get_allowance(self, token_data, spender) -> Optional[TokenAmount]:
        abi = token_data.get('abi')
        decimals = token_data.get('decimals')
        token_address = token_data.get('address')
        contract = Contract(address=token_address, abi=abi,
                            provider=self.account)
        allowance_check = await contract.functions['allowance'].prepare(owner=self.address,
                                                                        spender=spender).call()

        if token_address == 0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3:
            amount = allowance_check.res
        else:
            amount = allowance_check.remaining

        return TokenAmount(amount=amount, decimals=decimals, wei=True)


    @check_gas("starknet")
    async def call(self,
                   call_data: list,
                   cairo_version = CURRENT_ACCOUNTS_CAIRO_VERSION):
        for _ in range(10):
            try:
                logger.debug(f"[{self.address}] Sending tx...")
                tx_response = await self.account.execute(calls=call_data,
                                                         auto_estimate=True,
                                                         cairo_version=cairo_version)
                tx = await self.account.client.wait_for_tx(tx_response.transaction_hash)
                for _ in range(300):
                    try:
                        receipt = await self.account.client.get_transaction_receipt(tx.transaction_hash)
                        block = receipt.block_number
                        if block:
                            return True
                    except:
                        pass
                    finally:
                        await asyncio.sleep(2.5)
            except Exception as exc:
                logger.error(f"Couldn't send tx: {exc}")


    async def upgrade_contract(self) -> bool:
        try:
            logger.debug(f"[{self.address}] Upgrading contract...")
            contract = Contract(address=self.address, provider=self.account, abi=DefaultContractData.UPGRADE_ABI.get('abi'))
            call_data = [contract.functions["upgrade"].prepare(
                                                  implementation=DefaultContractData.ARGENT_X_CONTRACT_FOR_UPGRADE.get('address'),
                                                  calldata=[0])]
            tx_hash = await self.call(call_data, cairo_version=0)
            if tx_hash:
                logger.success(f"[{self.address}] Successfully upgraded contract...")
                return True
        except Exception as exc:
            logger.error(f"[{self.address}] Couldn't upgrade contract | {exc}")

    def get_eth_price(self, token='ETH') -> float:
        token = token.upper()
        logger.info(f'[{self.address}] | Getting {token} price')
        response = requests.get(f'https://api.binance.com/api/v3/depth?limit=1&symbol={token}USDT')
        if response.status_code != 200:
            logger.warning(f'code: {response.status_code} | json: {response.json()}')
            return 0
        result_dict = response.json()
        if 'asks' not in result_dict:
            logger.warning(f'code: {response.status_code} | json: {response.json()}')
            return 0
        return float(result_dict['asks'][0][0])
