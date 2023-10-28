from enum import Enum
from typing import List


class StarknetActions(Enum):
    '''Действия в Starknet'''
    MYSWAP = 1 
    JEDISWAP = 2
    AVNU = 3
    SITHSWAP = 4
    PROTOSS = 5
    FIBROUS = 6
    SWAP_10K = 7
    MINT_STARKNET = 8
    MINT_PYRAMID = 9
    DMAIL = 10
    LIQUIDITY_JEDISWAP = 11


class ErrorCodes(Enum):
    '''Коды ошибок'''
    SUCCESS = 200
    ERROR = 400
