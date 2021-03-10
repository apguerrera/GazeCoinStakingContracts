from brownie import accounts, web3, Wei, chain
from brownie.network.transaction import TransactionReceipt
from brownie.convert import to_address
import pytest
from brownie import Contract
from settings import *


@pytest.fixture(scope='module', autouse=True)
def gaze_coin(FixedToken):
    gaze_coin = FixedToken.deploy({"from":accounts[0]})
    name = "Gaze Coin"
    symbol = "GAC"
    gaze_coin.initToken(name, symbol, GAZE_TOTAL_TOKENS,{"from": accounts[0]})

    return gaze_coin

@pytest.fixture(scope='module', autouse=True)
def weth_token(WETH9):
    weth_token = WETH9.deploy({'from': accounts[0]})
    return weth_token

@pytest.fixture(scope='module', autouse=True)
def lp_token(FixedToken):
    lp_token_holder = accounts[5]
    lp_token = FixedToken.deploy({"from":lp_token_holder})
    name = "GAZE LP TOKEN"
    symbol = "GLT"
    lp_token.initToken(name, symbol, GAZE_TOTAL_TOKENS,{"from": lp_token_holder})

    return lp_token

@pytest.fixture(scope='module', autouse=True)
def gaze_stake_lp(GazeLPStaking,gaze_coin,lp_token,weth_token):
    gaze_stake_lp = GazeLPStaking.deploy({'from':accounts[0]})

    gaze_stake_lp.initLPStaking(gaze_coin,lp_token,weth_token, {"from":accounts[0]})

    return gaze_stake_lp
