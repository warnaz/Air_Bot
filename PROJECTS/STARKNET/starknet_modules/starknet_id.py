import random
from loguru import logger
from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.client_models import Call

from utils.gas_checker import check_gas
from utils.helpers import retry
from . import Starknet
from config import STARKNET_ID_CONTRACT


class StarknetId(Starknet):
    def __init__(self, _id: int, private_key: str, type_account: str) -> None:
        super().__init__(_id=_id, private_key=private_key, type_account=type_account)

    @retry
    @check_gas("starknet")
    async def mint(self):
        logger.info(f"[{self._id}][{hex(self.address)}] Start mint Starknet ID")

        mint_starknet_id_call = Call(
            to_addr=STARKNET_ID_CONTRACT,
            selector=get_selector_from_name("mint"),
            calldata=[int(random.random() * 1e12)],
        )

        transaction = await self.sign_transaction([mint_starknet_id_call])

        transaction_response = await self.send_transaction(transaction)

        await self.wait_until_tx_finished(transaction_response.transaction_hash)
