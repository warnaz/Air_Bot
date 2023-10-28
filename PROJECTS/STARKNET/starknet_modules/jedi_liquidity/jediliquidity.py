import asyncio
from random import choice, uniform
import random
from time import time
from loguru import logger
from dataclasses import dataclass
from starknet_modules.jedi_liquidity.path import *
import json
from starknet_modules.starknet import Starknet
from client import Client
from config import *
from starknet_modules.jedi_liquidity.default_data import DefaultContractData, TokenAmount
from starknet_modules.jedi_liquidity.default_data import get_data_for_liquidity_pool
from starknet_py.contract import Contract


class JediSwapLiquidity(Client, Starknet):
    def __init__(self, _id: int, private_key: str, type_account: str) -> None:
        super().__init__(_id=_id, private_key=private_key, type_account=type_account)

        self.contract = Contract(address=JediSwapLiquidity.JEDISWAP_CONTRACT, abi=JediSwapLiquidity.JEDISWAP_ABI, provider=self.account)

    ETH_ADDRESS = DefaultContractData.TOKEN_ADDRESSES.get('ETH').get('address')
    ETH_ABI = DefaultContractData.TOKEN_ADDRESSES.get('ETH').get('abi')

    USDT_ADDRESS = DefaultContractData.TOKEN_ADDRESSES.get('USDT').get('address')
    USDT_ABI = DefaultContractData.TOKEN_ADDRESSES.get('USDT').get('abi')

    USDC_ADDRESS = DefaultContractData.TOKEN_ADDRESSES.get('USDC').get('address')
    USDC_ABI = DefaultContractData.TOKEN_ADDRESSES.get('USDC').get('abi')

    DAI_ADDRESS = DefaultContractData.TOKEN_ADDRESSES.get('DAI').get('address')
    DAI_ABI = DefaultContractData.TOKEN_ADDRESSES.get('DAI').get('abi')

    JEDISWAP_CONTRACT = DefaultContractData.JEDISWAP_CONTRACT.get('address')
    JEDISWAP_ABI = DefaultContractData.JEDISWAP_CONTRACT.get('abi')

    JEDISWAP_ETHUSDC_CONTRACT = DefaultContractData.JEDISWAP_ADDRESSES.get('ETHUSDC').get('address')
    JEDISWAP_ETHUSDT_CONTRACT = DefaultContractData.JEDISWAP_ADDRESSES.get('ETHUSDT').get('address')

    JEDISWAP_USDCUSDT_CONTRACT = DefaultContractData.JEDISWAP_ADDRESSES.get('USDCUSDT').get('address')

    JEDISWAP_DAIETH_CONTRACT = DefaultContractData.JEDISWAP_ADDRESSES.get('DAIETH').get('address')
    JEDISWAP_DAIUSDT_CONTRACT = DefaultContractData.JEDISWAP_ADDRESSES.get('DAIUSDT').get('address')
    JEDISWAP_DAIUSDC_CONTRACT = DefaultContractData.JEDISWAP_ADDRESSES.get('DAIUSDC').get('address')

    async def add_liquidity(self, data: str) -> bool:
        try:
            get_data_for_adding_liquidity = await get_data_for_liquidity_pool(client=self, dex_name='jediswap', data=data)

            pooled_token_address, pooled_token_name, amount_one, amount_two, amount_in_usdt, token_one_address, token_two_address, token_one_name, token_two_name, token_one_decimals, token_two_decimals = get_data_for_adding_liquidity.values()
            
            balanceOne = await self.get_balance(token_address=token_one_address, decimals=token_one_decimals)
            balanceTwo = await self.get_balance(token_address=token_two_address, decimals=token_two_decimals)
        
            amount_one = TokenAmount(amount=amount_one, decimals=token_one_decimals)
            amount_two = TokenAmount(amount=amount_two, decimals=token_two_decimals)
            logger.debug(f"[{self.address}] Adding liquidity to {pooled_token_name} pool {amount_one.Ether} {token_one_name}...[JediSwap]")

            is_approved_one = await self.approve_interface(token_name=token_one_name,
                                                              spender=JediSwapLiquidity.JEDISWAP_CONTRACT,
                                                              decimals=token_one_decimals, amount=amount_one)

            is_approved_two = await self.approve_interface(token_name=token_two_name,
                                                              spender=JediSwapLiquidity.JEDISWAP_CONTRACT,
                                                              decimals=token_two_decimals, amount=amount_two)
            if is_approved_one and is_approved_two:
                call_data = [self.contract.functions['add_liquidity'].prepare(tokenA :=token_one_address,
                                                             tokenB :=token_two_address,
                                                             amountADesired :=amount_one.Wei,
                                                             amountBDesired :=amount_two.Wei,
                                                             amountAMin :=int(amount_one.Wei * (1 - SLIPPAGE/ 100)),
                                                             amountBMin :=int(amount_two.Wei * (1 - SLIPPAGE/ 100)),
                                                             to :=self.address,
                                                             deadline :=int(time() + 3600))]
                tx_hash = await self.call(call_data)
                if tx_hash:
                    logger.success(
                        f"[{self.address}] Successfully added ${amount_in_usdt} to {pooled_token_name} pool | [JediSwap]")
                    random_sleep = random.randint(DELAY_BETWEEN_ACTIONS[0], DELAY_BETWEEN_ACTIONS[1])
                    logger.info(f"[{self.address}] Sleeping for {random_sleep} sec before removing liquidity | [JediSwap]")
                    await asyncio.sleep(random_sleep)
                    for _ in range(5):
                        try:
                            if await self.remove_liquidity(token_one_address=token_one_address,
                                                        token_two_address=token_two_address,
                                                        pooled_token_name=pooled_token_name,
                                                        pooled_token_contract=pooled_token_address,
                                                        amountA=int(amount_one.Wei * (1 - SLIPPAGE/ 100)),
                                                        amountB=int(amount_two.Wei * (1 - SLIPPAGE/ 100))):
                                return True
                        except:
                            pass
        except Exception as exc:
            logger.error(f"[{self.address}] Couldn't add $ to pool | [JediSwap] | {exc}")

    async def remove_liquidity(
            self, 
            token_one_address, 
            token_two_address, 
            pooled_token_name,
            pooled_token_contract, 
            amountA = None, 
            amountB = None
        ) -> bool:
        try:
            logger.debug(
                f"[{self.address}] Removing liquidity | [JediSwap]")
            amount: TokenAmount = await self.get_balance(token_address=pooled_token_contract, decimals=18)

            tokenA = token_one_address
            tokenB = token_two_address

            is_approved = await self.approve_interface(token_name=pooled_token_name,
                                                              spender=JediSwapLiquidity.JEDISWAP_CONTRACT,
                                                              decimals=18, amount=amount)
            if is_approved:
                call_data = [self.contract.functions['remove_liquidity'].prepare(tokenA :=tokenA,
                                                             tokenB :=tokenB,
                                                             liquidity :=amount.Wei,
                                                             amountAMin :=amountA,
                                                             amountBMin :=amountB,
                                                             to :=self.address,
                                                             deadline :=int(time() + 3600))]
                tx_hash = await self.call(call_data)
                if tx_hash:
                    logger.success(
                        f"[{self.address}] Successfully removed liquidity | [JediSwap]")
                    return True
        except Exception as exc:
            logger.error(f"[{self.address}] Couldn't remove liquidity | [JediSwap] {exc}")
