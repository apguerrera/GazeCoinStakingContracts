from brownie import *
from .settings import *
from .contracts import *
from .contract_addresses import *

def main():
    load_accounts()
    access_control = deploy_access_controls()
    deploy_btts_lib()
    gaze_coin = deploy_gaze_coin(GAZE_COIN_NAME,GAZE_COIN_SYMBOL,GAZE_COIN_INITIAL_SUPPLY)

    weth_token = deploy_weth_token()
    lp_token = deploy_uniswap_pool(gaze_coin, weth_token)
    print("Uniswap Pool Token (LP): ", str(lp_token))

    gaze_staking = deploy_gaze_staking()

    rewards_contract = deploy_rewards_contract(access_control,GAZE_COIN_REWARDS_PER_BLOCK,gaze_staking)
    rewards_contract.setLPBonus(len(chain)+4990,1,{"from":accounts[0]})
    start_block = len(chain)


    gaze_coin.approve(gaze_staking,ONE_MILLION*TENPOW18, {'from':accounts[0]})
    gaze_coin.transfer(gaze_staking,ONE_MILLION * TENPOW18,{'from':accounts[0]})

    gaze_staking.initLPStaking(gaze_coin,lp_token,weth_token,access_control,start_block,{"from":accounts[0]})
    gaze_staking.setRewardsContract(rewards_contract,{"from":accounts[0]})