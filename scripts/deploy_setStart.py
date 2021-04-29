from brownie import *

from brownie import network
from brownie.network.gas.strategies import GasNowScalingStrategy
from brownie.network import gas_price
from .settings import *
from .contracts import *
from .contract_addresses import *
import time

from .deploy_setRewards import *
from .deploy_setBonus import *

def main():
    # Acocunts
    load_accounts()

    gas_strategy = GasNowScalingStrategy("fast", increment=1.2)
    gas_price(gas_strategy)

    # Get Contracts 
    rewards = get_rewards()

    # # Set Tokens Claimable
    start_time = 1619654400
    last_reward_time = 0

    rewards.setStartTime(start_time, last_reward_time, {'from':accounts[0]})
