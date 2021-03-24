from brownie import accounts, web3, Wei, chain, reverts
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
    lp_token.approve(gaze_stake_lp,staking_amount,{"from":lp_token_staker})
    before_stake_lp_balance = lp_token.balanceOf(lp_token_staker)
    
    
    gaze_stake_lp.stake(staking_amount, {"from":lp_token_staker})
    after_stake_lp_balance = lp_token.balanceOf(lp_token_staker)
    assert before_stake_lp_balance - after_stake_lp_balance  == staking_amount
    
    
    chain.mine(500)
    print(chain[-1].number)
    print('lenght of chain -',len(chain))
    unstaking_amount = 25 * TENPOW18
    before_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)
    tx = gaze_stake_lp.unstake(unstaking_amount, {"from":lp_token_staker})
    after_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)
    assert after_stake_rewards_balance -  before_stake_rewards_balance == 500

    chain.mine(499)


    before_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)
    tx = gaze_stake_lp.unstake(unstaking_amount, {"from":lp_token_staker})
    after_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)
    assert after_stake_rewards_balance -  before_stake_rewards_balance == 500
    #assert after_stake_rewards_balance -  before_stake_rewards_balance == 500

## TODO: Try staking with multiple stakers and check rewards

def test_lp_staking_multiple(lp_token,gaze_stake_lp,gaze_coin):
    for i in range(5):
        transfer_amount = 50 * TENPOW18
        transfer_to = accounts[i]
        owner = accounts[5]

        lp_token.approve(transfer_to,transfer_amount,{"from":owner})
        lp_token.transfer(transfer_to,transfer_amount,{"from":owner})
        
    # Staking
    for i in range(5):
        lp_token_staker = accounts[i]
        staking_amount = 50 * TENPOW18

        lp_token.approve(gaze_stake_lp,staking_amount,{"from":lp_token_staker})

        before_stake_lp_balance = lp_token.balanceOf(lp_token_staker)

        gaze_stake_lp.stake(staking_amount, {"from":lp_token_staker})

        after_stake_lp_balance = lp_token.balanceOf(lp_token_staker)

        assert before_stake_lp_balance - after_stake_lp_balance  == staking_amount

    chain.mine(500)

    # Unstaking 1/2
    for i in range(5):
        lp_token_staker = accounts[i]
        unstaking_amount = 25 * TENPOW18

        before_unstake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)

        gaze_stake_lp.unstake(unstaking_amount, {"from":lp_token_staker})

        after_unstake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)

        assert after_unstake_rewards_balance - before_unstake_rewards_balance == 100

    chain.mine(500)

    # Unstaking 2/2
    for i in range(5):
        lp_token_staker = accounts[i]
        unstaking_amount = 25 * TENPOW18

        before_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)

        gaze_stake_lp.unstake(unstaking_amount, {"from":lp_token_staker})

        after_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)

        assert after_stake_rewards_balance -  before_stake_rewards_balance == 100

def test_staking_and_then_complete_unstaking(lp_token,gaze_stake_lp,gaze_coin):
    lp_token_staker = accounts[5]
    staking_amount = 25 * TENPOW18
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
    staking_amount = 25* TENPOW18
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
    chain.mine(499)
    unstaking_amount = 50* TENPOW18
    before_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)
    tx = gaze_stake_lp.unstake(unstaking_amount, {"from":lp_token_staker})
    after_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)
  #  assert after_stake_rewards_balance -  before_stake_rewards_balance == (math.floor(500/25) + math.floor(500/75)) * 50

    lp_token_staker = accounts[5]
    unstaking_amount = 25* TENPOW18
    before_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)
    tx = gaze_stake_lp.unstake(unstaking_amount, {"from":lp_token_staker})
    after_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)
   # assert after_stake_rewards_balance -  before_stake_rewards_balance == (math.floor(500/25) + math.floor(500/75)) * 25

def test_emergency_unstake(lp_token,gaze_stake_lp,gaze_coin):
    lp_token_staker = accounts[5]
    staking_amount = 50* TENPOW18
    lp_token.approve(gaze_stake_lp,staking_amount,{"from":lp_token_staker})
    before_stake_lp_balance = lp_token.balanceOf(lp_token_staker)
    gaze_stake_lp.stake(staking_amount, {"from":lp_token_staker})
    after_stake_lp_balance = lp_token.balanceOf(lp_token_staker)
    assert before_stake_lp_balance - after_stake_lp_balance  == staking_amount
    
    chain.mine(500)

    before_unstake_lp_balance = lp_token.balanceOf(lp_token_staker)
    gaze_stake_lp.emergencyUnstake({"from":lp_token_staker})
    after_unstake_lp_balance = lp_token.balanceOf(lp_token_staker)
    assert after_unstake_lp_balance - before_unstake_lp_balance == staking_amount


def test_lp_staking_limited_rewards(lp_token,gaze_stake_lp_limited_rewards,gaze_coin):
    lp_token_staker = accounts[5]
    staking_amount = 50* TENPOW18
    lp_token.approve(gaze_stake_lp_limited_rewards,staking_amount,{"from":lp_token_staker})
    before_stake_lp_balance = lp_token.balanceOf(lp_token_staker)
    gaze_stake_lp_limited_rewards.stake(staking_amount, {"from":lp_token_staker})
    after_stake_lp_balance = lp_token.balanceOf(lp_token_staker)
    assert before_stake_lp_balance - after_stake_lp_balance  == staking_amount
    
    
    chain.mine(1000)

    unstaking_amount = 25* TENPOW18
    print(gaze_stake_lp_limited_rewards.balanceOfGazeCoin())
    #with reverts("GazeRewards.accumulatedLPRewards: No rewards to distribute"):
    tx = gaze_stake_lp_limited_rewards.unstake(unstaking_amount, {"from":lp_token_staker})
    print(gaze_stake_lp_limited_rewards.balanceOfGazeCoin())
    with reverts("GazeRewards.accumulatedLPRewards: No rewards to distribute"):
      tx = gaze_stake_lp_limited_rewards.unstake(unstaking_amount, {"from":lp_token_staker})
#########################
# Helper Function
#########################
@pytest.fixture(scope='function',autouse = True)
def gaze_stake_lp_limited_rewards(GazeLPStaking,gaze_coin,lp_token,weth_token,access_controls):
    gaze_stake_lp_limited_rewards = GazeLPStaking.deploy({'from':accounts[0]})
    
    gaze_coin.approve(gaze_stake_lp_limited_rewards,500 ,{'from':accounts[0]})
    gaze_coin.transfer(gaze_stake_lp_limited_rewards,500,{'from':accounts[0]})
    
    
    assert gaze_coin.balanceOf(gaze_stake_lp_limited_rewards) == 500
    gaze_stake_lp_limited_rewards.initLPStaking(gaze_coin,lp_token,weth_token,access_controls,len(chain),{"from":accounts[0]})

    gaze_stake_lp_limited_rewards.setTokensClaimable(True,{"from":accounts[0]})
    
    return gaze_stake_lp_limited_rewards 

@pytest.fixture(scope = 'function', autouse = True)
def rewards_contract_limited_rewards(GazeRewards,access_controls,gaze_stake_lp_limited_rewards):
    rewards_contract_limited_rewards = GazeRewards.deploy(access_controls,1,gaze_stake_lp_limited_rewards,{"from":accounts[0]})
    rewards_contract_limited_rewards.setLPBonus(len(chain)+5000,1,{"from":accounts[0]})
    gaze_stake_lp_limited_rewards.setRewardsContract(rewards_contract_limited_rewards,{"from":accounts[0]})
    return rewards_contract_limited_rewards

#################################
##### ZAP Test Needs Forking
#################################
""" def test_zap_lp_staking(GazeLPStaking,gaze_coin,lp_token_from_fork,weth_token,access_controls):
    gaze_stake_lp = gaze_stake_lp_from_fork(GazeLPStaking,gaze_coin,lp_token_from_fork,weth_token,access_controls)
    lp_token_staker = accounts[5]
    staking_amount = 5 * TENPOW18
    before_stake_lp_balance = lp_token_from_fork.balanceOf(lp_token_staker)
    gaze_stake_lp.zapEth({"from":lp_token_staker,"value":staking_amount})
    after_stake_lp_balance = lp_token_from_fork.balanceOf(lp_token_staker)
    assert before_stake_lp_balance - after_stake_lp_balance  == staking_amount
    
  

def gaze_stake_lp_from_fork(GazeLPStaking,gaze_coin,lp_token_from_fork,weth_token,access_controls):
    gaze_stake_lp = GazeLPStaking.deploy({'from':accounts[0]})
    chain.mine(5)
    
    gaze_coin.approve(gaze_stake_lp,ONE_MILLION * TENPOW18,{'from':accounts[0]})
    gaze_coin.transfer(gaze_stake_lp,ONE_MILLION * TENPOW18,{'from':accounts[0]})
    
    
    assert gaze_coin.balanceOf(gaze_stake_lp) == ONE_MILLION * TENPOW18
    gaze_stake_lp.initLPStaking(gaze_coin,lp_token_from_fork,weth_token,access_controls,len(chain),{"from":accounts[0]})

    gaze_stake_lp.setTokensClaimable(True,{"from":accounts[0]})
    
    return gaze_stake_lp """