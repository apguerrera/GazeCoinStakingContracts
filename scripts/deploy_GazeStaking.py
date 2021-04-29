from brownie import *
from .settings import *
from .contracts import *
from .contract_addresses import *
from .deploy_setRewards import *
from .deploy_setBonus import *

def main():
    load_accounts()

    vault = accounts[0]
    if network.show_active() == 'mainnet':
        vault =  CONTRACTS[network.show_active()]["vault"]

    access_control = deploy_access_controls()
    if access_control.hasAdminRole(vault) == False:
        access_control.addAdminRole(vault, {"from":accounts[0]})

    gaze_coin = deploy_gaze_coin(GAZE_COIN_NAME,GAZE_COIN_SYMBOL,GAZE_COIN_INITIAL_SUPPLY)
    weth_token = deploy_weth_token()
    lp_token = deploy_uniswap_pool(gaze_coin, weth_token)

    print("Sushiswap Pool Token (LP): ", str(lp_token))

    lp_staking = deploy_lp_staking(gaze_coin,lp_token,weth_token,access_control)

    rewards = deploy_rewards(gaze_coin, lp_staking,access_control,REWARDS_START_TIME, REWARDS_LAST_UPDATE, REWARDS_LP_PAID )
    if rewards.weeklyRewardsPerSecond(0) == 0:
        # set_bonus(lp_staking, rewards)
        set_rewards(rewards)
        print("rewards per second for week[0] =",rewards.weeklyRewardsPerSecond(0)* 14*24*60*60 /TENPOW18)
        print("rewards per second for week[8]=",rewards.weeklyRewardsPerSecond(8)* 14*24*60*60/TENPOW18)

    lp_staking.setRewardsContract(rewards,{"from":accounts[0]})
    rewards.setVault(vault, {"from":accounts[0]})

    # This needs to happen from the vault
    # gaze_coin.approve(rewards,ONE_MILLION, {'from':vault})

    lp_staking.setTokensClaimable(True, {"from":accounts[0]})

    