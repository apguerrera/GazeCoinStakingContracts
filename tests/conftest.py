from brownie import accounts, web3, Wei, chain
from brownie.network.transaction import TransactionReceipt
from brownie.convert import to_address
import pytest
from brownie import Contract
from settings import *


@pytest.fixture(scope='module',autouse= True)
def access_control(GazeAccessControls):
    access_control = GazeAccessControls.deploy({"from":accounts[0]}) 
    return access_control


@pytest.fixture(scope='module', autouse=True)
def btts_lib(BTTSLib):
    btts_lib = BTTSLib.deploy({'from': accounts[0]})
    return btts_lib

@pytest.fixture(scope='module', autouse=True)
def gaze_coin(BTTSToken, btts_lib):
    name = "GazeCoin Metaverse Token"
    symbol = "GZE"
    owner = accounts[1]
    initialSupply = 29000000 * 10 ** 18
    gaze_coin = BTTSToken.deploy(owner,symbol, name, 18, initialSupply, False, True, {"from":owner})

    return gaze_coin

@pytest.fixture(scope='module', autouse=True)
def weth_token(WETH9):
    weth_token = WETH9.deploy({'from': accounts[0]})
    return weth_token

@pytest.fixture(scope='module', autouse=True)
def lp_factory(UniswapV2Factory):
    
    lp_factory = UniswapV2Factory.deploy(accounts[0], {'from': accounts[0]})
    return lp_factory

@pytest.fixture(scope='module', autouse=True)
def lp_token(UniswapV2Pair, weth_token, gaze_coin):
    lp_token_deployer = accounts[5]
    lp_token = UniswapV2Pair.deploy({"from":lp_token_deployer})

    lp_token.initialize(weth_token, gaze_coin, {"from": lp_token_deployer})

    weth_token.deposit({'from': accounts[0], 'value': 1 * 10**18})
    gaze_coin.transfer(lp_token, 100000 * 10**18, {'from':accounts[1]})
    weth_token.transfer( lp_token,1 * 10**18,{'from':accounts[0]})
    lp_token.mint(accounts[0],{'from':accounts[0]})

    return lp_token

""" @pytest.fixture(scope='module', autouse=True)
def lp_token_from_fork(gaze_coin,weth_token,interface):
    uniswap_factory = interface.IUniswapV2Factory(UNISWAP_FACTORY)
    tx = uniswap_factory.createPair(gaze_coin, weth_token, {'from': accounts[0]})
    assert 'PairCreated' in tx.events
    lp_token_from_fork = interface.IUniswapV2Pair(web3.toChecksumAddress(tx.events['PairCreated']['pair']))
    return lp_token_from_fork """

@pytest.fixture(scope='module', autouse=True)
def lp_staking(GazeLPStaking,gaze_coin,lp_token,weth_token,access_control):
    lp_staking = GazeLPStaking.deploy({'from':accounts[0]})
    lp_staking.initLPStaking(gaze_coin,lp_token,weth_token,access_control,{"from":accounts[0]})

    lp_staking.setTokensClaimable(True)

    return lp_staking



##############################################
# Rewards
##############################################

@pytest.fixture(scope = 'module', autouse = True)
def rewards_contract(GazeRewards,access_control,gaze_coin, lp_staking):
    vault = accounts[1]
    rewards_contract = GazeRewards.deploy(gaze_coin,
                                        access_control,
                                        lp_staking,
                                        chain.time() +10,
                                        0,
                                        0,
                                        {'from': accounts[0]})



    return rewards_contract


@pytest.fixture(scope='module', autouse=True)
def staking_rewards(GazeLPStaking, GazeRewards, gaze_coin, lp_token, weth_token, access_control):
    staking_rewards = GazeLPStaking.deploy({'from':accounts[0]})
    staking_rewards.initLPStaking(gaze_coin,lp_token,weth_token,access_control,{"from":accounts[0]})

    vault = accounts[1]
    rewards_contract = GazeRewards.deploy(gaze_coin,
                                        access_control,
                                        staking_rewards,
                                        chain.time() +10,
                                        0,
                                        0,
                                        {'from': accounts[0]})


    assert gaze_coin.balanceOf(vault) > 0
    gaze_coin.approve(rewards_contract,ONE_MILLION,{"from":vault} )
    rewards_contract.setVault(vault,{"from":accounts[0]})

    staking_rewards.setRewardsContract(rewards_contract,{"from":accounts[0]})
    staking_rewards.setTokensClaimable(True,{"from":accounts[0]})

    weeks = [0,1,2,3,4,5]
    rewards = [70000*TENPOW18,60000*TENPOW18,50000*TENPOW18,50000*TENPOW18,45000*TENPOW18,42000*TENPOW18]
    rewards_contract.setRewards(weeks,rewards)

    chain.sleep(20)
    chain.mine()

    return staking_rewards

