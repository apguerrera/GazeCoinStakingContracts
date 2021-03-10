from brownie import accounts, web3, Wei, chain
from brownie.network.transaction import TransactionReceipt
from brownie.convert import to_address
import pytest
from brownie import Contract
from settings import *

@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass

#@pytest.fixture(scope='module')
#def populate_lp_token_to_accounts(lp_token):
#    lp_token.approve()

def test_lp_staking(lp_token,gaze_stake_lp):
    lp_token_holder = accounts[5]
    staking_amount = 50 * TENPOW18
    lp_token.approve(gaze_stake_lp,staking_amount,{"from":lp_token_holder})
    gaze_stake_lp.stake(staking_amount, {"from":lp_token_holder})