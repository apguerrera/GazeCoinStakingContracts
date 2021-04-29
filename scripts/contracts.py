from brownie import *
from .settings import *
from .contract_addresses import *

def load_accounts():
    if network.show_active() == 'mainnet':
        # replace with your keys
        accounts.load("gaze")
    # add accounts if active network is goerli
    if network.show_active() in ['goerli', 'ropsten','kovan','rinkeby']:
        # 0xa5C9fb5D557daDb10c4B5c70943d610001B7420E 
        accounts.add('6a202283db75b6ea23175f3c795d4e73154a28bd7e72ec0d31a8ab76f9d80200')
        # 0x9135C43D7bA230d372A12B354c2E2Cf58b081463
        accounts.add('6a202283db75b6ea23175f3c795d4e73154a28bd7e72ec0d31a8ab76f9d80201')

def publish():
    if network.show_active() == "development":
        return False 
    else:
        return True


def deploy_access_controls():
    access_control_address = CONTRACTS[network.show_active()]["access_control"]
    if access_control_address == '':
        access_control = GazeAccessControls.deploy({"from":accounts[0]}, publish_source=publish())
    else:
        access_control = GazeAccessControls.at(access_control_address)
    return access_control

def deploy_gaze_coin(name, symbol, initialSupply):
    gaze_coin_address = CONTRACTS[network.show_active()]["gaze_coin"]
    if gaze_coin_address == '':
        owner = accounts[0]
        deploy_btts_lib()
        gaze_coin = BTTSToken.deploy(owner,symbol, name, 18, initialSupply, False, True, {"from":owner}, publish_source=publish())
    else:
        gaze_coin = BTTSToken.at(gaze_coin_address)
    return gaze_coin

def get_gaze_coin():
    gaze_coin_address = CONTRACTS[network.show_active()]["gaze_coin"]
    return GazeCoin.at(gaze_coin_address) 
        
def deploy_weth_token():
    weth_token_address = CONTRACTS[network.show_active()]["weth"]
    if weth_token_address == '':
        weth_token = WETH9.deploy({'from': accounts[0]}, publish_source=publish())
    else:
        weth_token = WETH9.at(weth_token_address)
    return weth_token


def deploy_uniswap_pool(tokenA, tokenB):
    uniswap_pool_address = CONTRACTS[network.show_active()]["lp_token"]
    sushi_factory_address = CONTRACTS[network.show_active()]["sushi_factory"]

    if uniswap_pool_address == '':
        #For local development network:
        if network.show_active() == 'development':
            uniswap_factory = UniswapV2Factory.deploy(accounts[5],{"from":accounts[0]}, publish_source=publish())
        else:
            uniswap_factory = interface.IUniswapV2Factory(sushi_factory_address)
        tx = uniswap_factory.createPair(tokenA, tokenB, {'from': accounts[0]})
        assert 'PairCreated' in tx.events
        uniswap_pool = interface.IUniswapV2Pair(web3.toChecksumAddress(tx.events['PairCreated']['pair']))
    else:
        uniswap_pool = interface.IUniswapV2Pair(uniswap_pool_address)
    return uniswap_pool


def deploy_rewards(rewards_token,lp_staking, access_control, start_time,last_time,lp_paid):
    rewards_address = CONTRACTS[network.show_active()]["rewards_contract"]
    if rewards_address == "":
        rewards = GazeRewards.deploy(rewards_token,
                                        access_control,
                                        lp_staking,
                                        start_time,
                                        last_time,
                                        lp_paid,
                                        {'from': accounts[0]}, publish_source=publish())
    else:
        rewards = GazeRewards.at(rewards_address)
    return rewards

def get_rewards():
    rewards_address = CONTRACTS[network.show_active()]["rewards_contract"]
    return GazeRewards.at(rewards_address) 

def deploy_lp_staking(rewards_token, lp_token,weth_token, access_control):
    lp_staking_address = CONTRACTS[network.show_active()]["lp_staking"]
    if lp_staking_address == "":
        lp_staking = GazeLPStaking.deploy({'from': accounts[0]}, publish_source=publish())
        lp_staking.initLPStaking(rewards_token, lp_token, weth_token, access_control,{'from': accounts[0]})
    else:
        lp_staking = GazeLPStaking.at(lp_staking_address)
    return lp_staking

def get_lp_staking():
    lp_staking_address = CONTRACTS[network.show_active()]["lp_staking"]
    return GazeLPStaking.at(lp_staking_address) 
        

def deploy_btts_lib():
    btts_lib_address = CONTRACTS[network.show_active()]["btts_lib"]
    if btts_lib_address == '':
        btts_lib = BTTSLib.deploy({'from': accounts[0]}, publish_source=publish())
    else: 
        btts_lib = BTTSLib.at(btts_lib_address)
    return btts_lib