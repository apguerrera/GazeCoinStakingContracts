from brownie import *
from .settings import *
from .contracts import *
from .contract_addresses import *
import time


def main():
    load_accounts()

    treasury = web3.toChecksumAddress('0x66d7Dd55646100541F2B6ec15781b6d4C8372b1c')
    gaze_coin = CONTRACTS[network.show_active()]["gaze_coin"]

    # Deploy Contracts 
   
  
    gaze_coin = deploy_gaze_coin(GAZE_COIN_NAME,GAZE_COIN_SYMBOL,GAZE_COIN_INITIAL_SUPPLY)
    weth_token = deploy_weth_token()

    # Deploy Uniswap Pool
    uniswap_pool = deploy_uniswap_pool(gaze_coin, weth_token)
    
    print(str(uniswap_pool))


