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
def lp_token(FixedToken):
    lp_token_deployer = accounts[5]
    lp_token = FixedToken.deploy({"from":lp_token_deployer})
    name = "GAZE LP TOKEN"
    symbol = "GLT"
    lp_token.initToken(name, symbol, ONE_MILLION * TENPOW18,{"from": lp_token_deployer})

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

    lp_staking.setRewardsContract(rewards_contract,{"from":accounts[0]})
    gaze_coin.approve(rewards_contract,ONE_MILLION,{"from":vault} )
    rewards_contract.setVault(vault,{"from":accounts[0]})
    lp_staking.setTokensClaimable(True,{"from":accounts[0]})

    return rewards_contract


@pytest.fixture(scope='module', autouse=True)
def staking_rewards(GazeRewards,gaze_coin,access_control,lp_staking):
    start_time = chain.time() 
    staking_rewards = GazeRewards.deploy(
                gaze_coin,
                access_control,
                lp_staking,
                start_time,
                0,0,
                {'from':accounts[0]}
    )

    vault = accounts[1]
    gaze_coin.approve(staking_rewards,ONE_MILLION,{"from":vault} )

    lp_staking.setRewardsContract(staking_rewards)

    weeks = [0,1,2,3,4,5]
    rewards = [700*TENPOW18,700*TENPOW18,500*TENPOW18,350*TENPOW18,150*TENPOW18,100*TENPOW18]
    staking_rewards.setRewards(weeks,rewards)

    chain.sleep(10000 +20)
    chain.mine()

    return staking_rewards
