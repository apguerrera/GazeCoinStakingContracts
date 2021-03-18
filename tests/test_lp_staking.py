from brownie import accounts, web3, Wei, chain
from brownie.network.transaction import TransactionReceipt
from brownie.convert import to_address
import pytest
from brownie import Contract
from settings import *
import math 
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass

#@pytest.fixture(scope='module')
#def populate_lp_token_to_accounts(lp_token):
#    lp_token.approve()

@pytest.fixture(scope='function')
def transfer_lp_tokens_to_multiple_accounts(lp_token):
  transfer_amount = 50 * TENPOW18
  transfer_to = accounts[4]
  owner = accounts[5]
  lp_token.approve(transfer_to,transfer_amount,{"from":owner})
  lp_token.transfer(transfer_to,transfer_amount,{"from":owner})

  transfer_amount = 50 * TENPOW18
  transfer_to = accounts[6]
  owner = accounts[5]
  lp_token.approve(transfer_to,transfer_amount,{"from":owner})
  lp_token.transfer(transfer_to,transfer_amount,{"from":owner})


def test_lp_staking(lp_token,gaze_stake_lp,gaze_coin):
    lp_token_staker = accounts[5]
    staking_amount = 50 * TENPOW18
  #  gaze_coin.approve(lp_token_staker,ONE_MILLION * TENPOW18,{'from':accounts[0]})
    lp_token.approve(gaze_stake_lp,staking_amount,{"from":lp_token_staker})
    before_stake_lp_balance = lp_token.balanceOf(lp_token_staker)

    gaze_stake_lp.stake(staking_amount, {"from":lp_token_staker})
    
    after_stake_lp_balance = lp_token.balanceOf(lp_token_staker)

    assert before_stake_lp_balance - after_stake_lp_balance  == staking_amount
    chain.mine(500)

    unstaking_amount = 25 * TENPOW18
    before_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)
    tx = gaze_stake_lp.unstake(unstaking_amount, {"from":lp_token_staker})
   
    after_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)

    assert after_stake_rewards_balance -  before_stake_rewards_balance == 500

    chain.mine(500)


    before_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)
    tx = gaze_stake_lp.unstake(unstaking_amount, {"from":lp_token_staker})
   
    after_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)
    assert after_stake_rewards_balance -  before_stake_rewards_balance == 500
    #assert after_stake_rewards_balance -  before_stake_rewards_balance == 500

## TODO: Try staking with multiple stakers and check rewards

def test_staking_and_then_complete_unstaking(lp_token,gaze_stake_lp,gaze_coin):
    lp_token_staker = accounts[5]
    staking_amount = 25 * TENPOW18
  #  gaze_coin.approve(lp_token_staker,ONE_MILLION * TENPOW18,{'from':accounts[0]})
    lp_token.approve(gaze_stake_lp,staking_amount,{"from":lp_token_staker})
    before_stake_lp_balance = lp_token.balanceOf(lp_token_staker)

    gaze_stake_lp.stake(staking_amount, {"from":lp_token_staker})
    
    after_stake_lp_balance = lp_token.balanceOf(lp_token_staker)

    assert before_stake_lp_balance - after_stake_lp_balance  == staking_amount
    chain.mine(500)
    unstaking_amount = 25 * TENPOW18
    before_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)
    tx = gaze_stake_lp.unstake(unstaking_amount, {"from":lp_token_staker})
   
    after_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)

    assert after_stake_rewards_balance -  before_stake_rewards_balance == 500
    assert gaze_stake_lp.stakers(lp_token_staker)[0] == 0
    assert gaze_stake_lp.stakers(lp_token_staker)[1] == 0

 
 

def test_multiple_staking(lp_token,gaze_stake_lp,gaze_coin,transfer_lp_tokens_to_multiple_accounts):
  ###########################
  # Staker accounts[5]
  ###########################

    lp_token_staker = accounts[5]
    staking_amount = 25 * TENPOW18
    lp_token.approve(gaze_stake_lp,staking_amount,{"from":lp_token_staker})
    before_stake_lp_balance = lp_token.balanceOf(lp_token_staker)

    gaze_stake_lp.stake(staking_amount, {"from":lp_token_staker})
    
    after_stake_lp_balance = lp_token.balanceOf(lp_token_staker)

    assert before_stake_lp_balance - after_stake_lp_balance  == staking_amount
    chain.mine(500)
  ###########################
  # Staker accounts[4]
  ###########################
    staking_amount = 50 * TENPOW18
    lp_token_staker = accounts[4]
    lp_token.approve(gaze_stake_lp,staking_amount,{"from":lp_token_staker})
    before_stake_lp_balance = lp_token.balanceOf(lp_token_staker)
    
    gaze_stake_lp.stakeAll({"from":lp_token_staker})
    
    after_stake_lp_balance = lp_token.balanceOf(lp_token_staker)

    assert before_stake_lp_balance - after_stake_lp_balance  == staking_amount
    
    lp_token_staker = accounts[4]
    chain.mine(500)

    unstaking_amount = 50 * TENPOW18
    before_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)
    tx = gaze_stake_lp.unstake(unstaking_amount, {"from":lp_token_staker})
   
    after_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)
    assert after_stake_rewards_balance -  before_stake_rewards_balance == (math.floor(500/25) + math.floor(500/75)) * 50

    lp_token_staker = accounts[5]
    
    unstaking_amount = 25 * TENPOW18
    before_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)
    tx = gaze_stake_lp.unstake(unstaking_amount, {"from":lp_token_staker})
   
    after_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)

    assert after_stake_rewards_balance -  before_stake_rewards_balance == (math.floor(500/25) + math.floor(500/75)) * 25