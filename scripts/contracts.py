from brownie import *
from .settings import *
from .contract_addresses import *

def load_accounts():
    if network.show_active() == 'mainnet':
        # replace with your keys
        accounts.load("digitalax")
    # add accounts if active network is goerli
    if network.show_active() in ['goerli', 'ropsten','kovan','rinkeby']:
        # 0x2A40019ABd4A61d71aBB73968BaB068ab389a636
        accounts.add('4ca89ec18e37683efa18e0434cd9a28c82d461189c477f5622dae974b43baebf')
        # 0x1F3389Fc75Bf55275b03347E4283f24916F402f7
        accounts.add('fa3c06c67426b848e6cef377a2dbd2d832d3718999fbe377236676c9216d8ec0')

def deploy_access_controls():
    access_control_address = CONTRACTS[network.show_active()]["access_control"]
    if access_control_address == '':
        access_control = GazeAccessControls.deploy({"from":accounts[0]})
    else:
        access_control = GazeAccessControls.at(access_control_address)
    return access_control

def deploy_gaze_coin():
    gaze_coin_address = CONTRACTS[network.show_active()]["gaze_coin"]
    if gaze_coin_address == '':
        name = "GazeCoin Metaverse Token"
        symbol = "GZE"
        owner = accounts[0]
        initialSupply = 29000000 * TENPOW18
        gaze_coin = BTTSToken.deploy(owner,symbol, name, 18, initialSupply, False, True, {"from":owner})
    else:
        gaze_coin = BTTSToken.at(gaze_coin_address)
    return gaze_coin

def get_gaze_coin():
    gaze_coin_address = CONTRACTS[network.show_active()]["gaze_coin"]
    return GazeCoin.at(gaze_coin_address) 
        
def deploy_weth_token():
    weth_token_address = CONTRACTS[network.show_active()]["weth"]
    if weth_token_address == '':
        weth_token = WETH9.deploy({'from': accounts[0]})
    else:
        weth_token = WETH9.at(weth_token_address)
    return weth_token


def deploy_uniswap_pool(tokenA, tokenB):
    uniswap_pool_address = CONTRACTS[network.show_active()]["lp_token"]
    if uniswap_pool_address == '':
        uniswap_factory = interface.IUniswapV2Factory(UNISWAP_FACTORY)
        tx = uniswap_factory.createPair(tokenA, tokenB, {'from': accounts[0]})
        assert 'PairCreated' in tx.events
        uniswap_pool = interface.IUniswapV2Pair(web3.toChecksumAddress(tx.events['PairCreated']['pair']))
    else:
        uniswap_pool = interface.IUniswapV2Pair(uniswap_pool_address)
    return uniswap_pool

def deploy_rewards_contract():
    rewards_contract_address = CONTRACTS[network.show_active()]["rewards_contract"]
    if rewards_contract_address == '':
        rewards_contract = GazeRewards.deploy({"from":accounts[0]})
    else:
        rewards_contract = GazeRewards.at(rewards_contract_address)
    return rewards_contract

#TODO deploy GazeLPStaking contract
    