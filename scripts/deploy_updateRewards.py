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

    # MONA Token
    access_control = deploy_access_control()
    gaze_token = get_gaze_token()

    # Get Contracts 
    lp_staking = get_lp_staking()
    rewards = get_rewards()

    # # Set Tokens Claimable

    lp_staking.setTokensClaimable(False, {'from':accounts[0]})

    # Accounting snapshot
    last_rewards = rewards.lastRewardTime({'from':accounts[0]})
    print("Last Rewards: ", str(last_rewards))

    lp_paid = rewards.lpRewardsPaid({'from':accounts[0]})
    print("Rewards Paid: LP:",str(lp_paid))

    # # Rewards Contract
    new_rewards = deploy_new_rewards(gaze_token,lp_staking,
                                    access_control,REWARDS_START_TIME, last_rewards, lp_paid)

    # Set weekly rewards
    set_rewards(new_rewards)
    print("rewards per second for week[0] =",new_rewards.weeklyRewardsPerSecond(0)* 14*24*60*60 /TENPOW18)
    print("rewards per second for week[8]=",new_rewards.weeklyRewardsPerSecond(8)* 14*24*60*60/TENPOW18)


    # Add Vault permissions 
    # access_control.addMinterRole(new_rewards, {'from': accounts[0]})

    # Set Rewards contract on staking pooks
    lp_staking.setRewardsContract(new_rewards,{'from': accounts[0]}) 

    # Set Tokens Claimable
    lp_staking.setTokensClaimable(True, {'from':accounts[0]})

    # Refresh the updated time to check it works
    new_rewards.updateRewards({'from': accounts[0]})
