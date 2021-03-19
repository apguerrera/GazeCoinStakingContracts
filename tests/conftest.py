from brownie import accounts, web3, Wei, chain
from brownie.network.transaction import TransactionReceipt
from brownie.convert import to_address
import pytest
from brownie import Contract
from settings import *


@pytest.fixture(scope='module',autouse= True)
def access_controls(GazeAccessControls):
    access_controls = GazeAccessControls.deploy({"from":accounts[0]}) 
    return access_controls


@pytest.fixture(scope='module', autouse=True)
def btts_lib(BTTSLib):
    btts_lib = BTTSLib.deploy({'from': accounts[0]})
    return btts_lib

@pytest.fixture(scope='module', autouse=True)
def gaze_coin(BTTSToken, btts_lib):
    name = "GazeCoin Metaverse Token"
    symbol = "GZE"
    owner = accounts[0]
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
    lp_token.initToken(name, symbol, GAZE_TOTAL_TOKENS,{"from": lp_token_deployer})

    return lp_token

@pytest.fixture(scope = 'module', autouse = True)
def rewards_contract(GazeRewards,access_controls):
    rewards_contract = GazeRewards.deploy(access_controls,1,{"from":accounts[0]})
    rewards_contract.setLPBonus(len(chain)+5000,1,{"from":accounts[0]})
    return rewards_contract

@pytest.fixture(scope='module', autouse=True)
def gaze_stake_lp(GazeLPStaking,gaze_coin,rewards_contract,lp_token,weth_token,access_controls):
    gaze_stake_lp = GazeLPStaking.deploy({'from':accounts[0]})
    chain.mine(5)
    
    gaze_coin.approve(gaze_stake_lp,ONE_MILLION * TENPOW18,{'from':accounts[0]})
    gaze_coin.transfer(gaze_stake_lp,ONE_MILLION * TENPOW18,{'from':accounts[0]})
    
    
    assert gaze_coin.balanceOf(gaze_stake_lp) == ONE_MILLION * TENPOW18
    gaze_stake_lp.initLPStaking(gaze_coin,lp_token,weth_token,access_controls,len(chain),{"from":accounts[0]})

    gaze_stake_lp.setTokensClaimable(True,{"from":accounts[0]})
    gaze_stake_lp.setRewardsContract(rewards_contract,{"from":accounts[0]})
    return gaze_stake_lp
