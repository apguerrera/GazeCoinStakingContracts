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
    lp_token_staker = accounts[5]
    lp_token = FixedToken.deploy({"from":lp_token_staker})
    name = "GAZE LP TOKEN"
    symbol = "GLT"
    lp_token.initToken(name, symbol, GAZE_TOTAL_TOKENS,{"from": lp_token_staker})

    return lp_token

@pytest.fixture(scope='module', autouse=True)
def gaze_stake_lp(GazeLPStaking,gaze_coin,lp_token,weth_token):
    gaze_stake_lp = GazeLPStaking.deploy({'from':accounts[0]})
    chain.mine(5)
    gaze_coin.approve(gaze_stake_lp,ONE_MILLION * TENPOW18,{'from':accounts[0]})
    gaze_coin.transfer(gaze_stake_lp,ONE_MILLION * TENPOW18,{'from':accounts[0]})
    assert gaze_coin.balanceOf(gaze_stake_lp) == ONE_MILLION * TENPOW18
    gaze_stake_lp.initLPStaking(gaze_coin,lp_token,weth_token, 1,{"from":accounts[0]})

    gaze_stake_lp.setTokensClaimable(True)
    return gaze_stake_lp
