from brownie import *
from .settings import *
from .contracts import *
from .contract_addresses import *
from .deploy_setRewards import *
from .deploy_setBonus import *

def main():
    load_accounts()

    vault = accounts[0]

    access_control = deploy_access_controls()
    gaze_coin = deploy_gaze_coin(GAZE_COIN_NAME,GAZE_COIN_SYMBOL,GAZE_COIN_INITIAL_SUPPLY)
    weth_token = deploy_weth_token()
    lp_token = deploy_uniswap_pool(gaze_coin, weth_token)

    print("Uniswap Pool Token (LP): ", str(lp_token))

    initial_eth = 0.0001*TENPOW18
    initial_gze = 10*TENPOW18

    weth_token.deposit({'from':accounts[0], "value":initial_eth})
    weth_token.transfer(lp_token, initial_eth, {'from':accounts[0]})
    gaze_coin.transfer(lp_token,initial_gze, {'from':accounts[0]})

    lp_token.mint(accounts[0],{'from':accounts[0]})