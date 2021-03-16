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

def test_lp_staking(lp_token,gaze_stake_lp,gaze_coin):
    lp_token_staker = accounts[5]
    staking_amount = 50 * TENPOW18
    gaze_coin.approve(lp_token_staker,ONE_MILLION * TENPOW18,{'from':accounts[0]})


    lp_token.approve(gaze_stake_lp,staking_amount,{"from":lp_token_staker})
    before_stake_lp_balance = lp_token.balanceOf(lp_token_staker)

    gaze_stake_lp.stake(staking_amount, {"from":lp_token_staker})
    
    after_stake_lp_balance = lp_token.balanceOf(lp_token_staker)

    assert before_stake_lp_balance - after_stake_lp_balance  == staking_amount
    chain.mine(500)

    tx = gaze_stake_lp.updateRewardPool(lp_token_staker)

    before_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)
    tx = gaze_stake_lp.unstake(staking_amount, {"from":lp_token_staker})
    after_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)

    assert after_stake_rewards_balance -  before_stake_rewards_balance == 500

## TODO: Try staking with multiple stakers and check rewards