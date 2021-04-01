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


# This is for a fixed dummy token, needs to be LP tokens
# @pytest.fixture(scope='function')
# def transfer_lp_tokens_to_multiple_accounts(lp_token):
#   transfer_amount = 50 * TENPOW18
#   transfer_to = accounts[4]
#   owner = accounts[5]
#   lp_token.approve(transfer_to,transfer_amount,{"from":owner})
#   lp_token.transfer(transfer_to,transfer_amount,{"from":owner})

#   transfer_amount = 50 * TENPOW18
#   transfer_to = accounts[6]
#   owner = accounts[5]
#   lp_token.approve(transfer_to,transfer_amount,{"from":owner})
#   lp_token.transfer(transfer_to,transfer_amount,{"from":owner})


@pytest.fixture(scope='module', autouse=True)
def rewards_contract(GazeRewards, staking_rewards):
    rewards_contract = GazeRewards.at(staking_rewards.rewardsContract())
    return rewards_contract

def stake(staking_rewards, staker, staking_amount):
    staking_rewards.stake(staking_amount, {"from": staker})
    staker_info = staking_rewards.stakers(staker)
    assert staker_info[0] == staking_amount


def test_lp_staking_zap(staking_rewards, lp_token, rewards_contract, weth_token, gaze_coin):
    staker = accounts[5]
    before_stake_lp_balance = staking_rewards.getStakedBalance(staker)
    
    eth_amount = 1 * TENPOW18
    staking_rewards.zapEth({"from":staker, 'value': eth_amount})
    after_stake_lp_balance = staking_rewards.getStakedBalance(staker)
    total_eth_staked = staking_rewards.stakedEthTotal()
    assert after_stake_lp_balance > before_stake_lp_balance
    
    chain.sleep(ONE_WEEK)
    
    # Unstaking

    unstaking_amount = staking_rewards.stakers(staker)[0]
    
    # updating staker info
    staking_rewards.updateReward(staker, {'from': staker}) 
    before_stake_rewards_balance = gaze_coin.balanceOf(staker)
    unclaimed_rewards_before = staking_rewards.unclaimedRewards(staker)
    
    tx = staking_rewards.unstake(unstaking_amount, {"from":staker})    
    after_stake_rewards_balance = gaze_coin.balanceOf(staker)

    assert "Unstaked" in tx.events
    assert after_stake_rewards_balance - before_stake_rewards_balance == unclaimed_rewards_before
    assert staking_rewards.unclaimedRewards(staker) == 0

def test_lp_staking_stake(staking_rewards, lp_token, rewards_contract, gaze_coin):
    staker = accounts[5]
    staking_amount = 100*TENPOW18

    lp_token.transfer(staker, staking_amount, {'from': accounts[0]})
    lp_token.approve(staking_rewards, staking_amount, {'from': staker})
    stake(staking_rewards, staker, staking_amount)

    chain.sleep(ONE_WEEK)

    # updating staker info
    staking_rewards.updateReward(staker, {'from': staker})
    print("current week:", rewards_contract.getCurrentWeek())
    print("LP Total Staked:", staking_rewards.stakedLPTotal())

    # Claiming reward
    unclaimed_rewards_before = staking_rewards.unclaimedRewards(staker)
    before_staker_rewards_balance = gaze_coin.balanceOf(staker)
    assert unclaimed_rewards_before > 0

    print("unclaimed amount", unclaimed_rewards_before)

    tx = staking_rewards.claimReward(staker, {'from': staker})
    staker_info = staking_rewards.stakers(staker)
    after_staker_rewards_balance = gaze_coin.balanceOf(staker)

    assert "RewardPaid" in tx.events
    assert staking_rewards.unclaimedRewards(staker) == 0
    assert unclaimed_rewards_before == staker_info[2]
    assert before_staker_rewards_balance+unclaimed_rewards_before == after_staker_rewards_balance


def test_lp_staking_unstake(staking_rewards, lp_token, rewards_contract, gaze_coin):
    staker = accounts[5]
    staking_amount = 50*TENPOW18
    lp_token.transfer(staker, staking_amount, {'from': accounts[0]})
    lp_token.approve(staking_rewards, staking_amount, {'from': staker})

    stake(staking_rewards, staker, staking_amount)

    chain.sleep(ONE_WEEK)

    # updating staker info
    staking_rewards.updateReward(staker, {'from': staker})

    unclaimed_rewards = staking_rewards.unclaimedRewards(staker)

    tx = staking_rewards.unstake(staking_amount, {'from': staker})
    staker_info = staking_rewards.stakers(staker)

    assert "Unstaked" in tx.events
    assert unclaimed_rewards == gaze_coin.balanceOf(staker)
    assert staker_info[0] == 0
    assert staker_info[1] == 0
    assert staker_info[2] == 0
    assert staker_info[3] == 0


def test_lp_staking_multiple(lp_token, staking_rewards, rewards_contract, gaze_coin):
    lp_token_owner = accounts[0]
    for i in range(2, 7):
        transfer_amount = 50 * TENPOW18
        transfer_to = accounts[i]

        lp_token.transfer(transfer_to, transfer_amount, {"from": lp_token_owner})
        
    # Staking
    for i in range(2, 7):
        staker = accounts[i]
        staking_amount = 50 * TENPOW18

        lp_token.approve(staking_rewards,staking_amount,{"from": staker})

        before_stake_lp_balance = lp_token.balanceOf(staker)

        stake(staking_rewards, staker, staking_amount)

        after_stake_lp_balance = lp_token.balanceOf(staker)

        assert before_stake_lp_balance - after_stake_lp_balance == staking_amount

    chain.sleep(ONE_WEEK)

    # Unstaking 1/2
    week_1_rewards = 700
    first_week_rewards_per_staker = week_1_rewards / 5 / 2 - 1 # TODO Question: Why do stakers get only half of rewards??
    for i in range(2, 7):
        staker = accounts[i]
        unstaking_amount = 25 * TENPOW18

        before_unstake_rewards_balance = gaze_coin.balanceOf(staker)

        staking_rewards.unstake(unstaking_amount, {"from":staker})

        after_unstake_rewards_balance = gaze_coin.balanceOf(staker)

        assert int(after_unstake_rewards_balance - before_unstake_rewards_balance) == int(first_week_rewards_per_staker)

    chain.sleep(ONE_WEEK)

    # Unstaking 2/2
    for i in range(2, 7):
        staker = accounts[i]
        unstaking_amount = 25 * TENPOW18

        before_stake_rewards_balance = gaze_coin.balanceOf(staker)

        staking_rewards.unstake(unstaking_amount, {"from": staker})

        after_stake_rewards_balance = gaze_coin.balanceOf(staker)

        assert int(after_stake_rewards_balance -  before_stake_rewards_balance) == int(first_week_rewards_per_staker)


def test_staking_and_then_complete_unstaking(lp_token, staking_rewards, gaze_coin):
    staker = accounts[5]
    staking_amount = 25 * TENPOW18

    lp_token.transfer(staker, staking_amount, {'from': accounts[0]})
    lp_token.approve(staking_rewards, staking_amount,{"from": staker})
    before_stake_lp_balance = lp_token.balanceOf(staker)

    staking_rewards.stake(staking_amount, {"from": staker})
    
    after_stake_lp_balance = lp_token.balanceOf(staker)

    assert before_stake_lp_balance - after_stake_lp_balance  == staking_amount
    chain.sleep(ONE_WEEK)
    unstaking_amount = 25 * TENPOW18
    before_stake_rewards_balance = gaze_coin.balanceOf(staker)
    tx = staking_rewards.unstake(unstaking_amount, {"from":staker})
   
    after_stake_rewards_balance = gaze_coin.balanceOf(staker)

    first_week_rewards_per_staker = 700 / 2 - 1
    assert after_stake_rewards_balance -  before_stake_rewards_balance == first_week_rewards_per_staker
    assert staking_rewards.stakers(staker)[0] == 0
    assert staking_rewards.stakers(staker)[1] == 0


def test_emergency_unstake(lp_token, staking_rewards, gaze_coin):
    staker = accounts[5]
    staking_amount = 50* TENPOW18

    lp_token.transfer(staker, staking_amount, {'from': accounts[0]})
    lp_token.approve(staking_rewards,staking_amount,{"from": staker})
    before_stake_lp_balance = lp_token.balanceOf(staker)
    staking_rewards.stake(staking_amount, {"from": staker})
    after_stake_lp_balance = lp_token.balanceOf(staker)
    assert before_stake_lp_balance - after_stake_lp_balance  == staking_amount
    
    chain.sleep(ONE_WEEK)

    before_unstake_lp_balance = lp_token.balanceOf(staker)
    staking_rewards.emergencyUnstake({"from":staker})
    after_unstake_lp_balance = lp_token.balanceOf(staker)
    assert after_unstake_lp_balance - before_unstake_lp_balance == staking_amount 
 
def test_staking_6_weeks(lp_token, staking_rewards, rewards_contract, gaze_coin):
    staker = accounts[5]
    staking_amount = 50* TENPOW18

    lp_token.transfer(staker, staking_amount, {'from': accounts[0]})
    lp_token.approve(staking_rewards,staking_amount,{"from": staker})

    stake(staking_rewards, staker, staking_amount)

    chain.sleep(ONE_WEEK*6)

    tx = staking_rewards.claimReward(staker, {'from': staker})
    staker_info = staking_rewards.stakers(staker)
    after_staker_rewards_balance = gaze_coin.balanceOf(staker)
    assert 1==2

# def test_multiple_staking(lp_token,lp_staking,gaze_coin,transfer_lp_tokens_to_multiple_accounts):
#   ###########################
#   # Staker accounts[5]
#   ###########################

#     lp_token_staker = accounts[5]
#     staking_amount = 25* TENPOW18
#     lp_token.approve(lp_staking,staking_amount,{"from":lp_token_staker})
#     before_stake_lp_balance = lp_token.balanceOf(lp_token_staker)
#     lp_staking.stake(staking_amount, {"from":lp_token_staker})
#     after_stake_lp_balance = lp_token.balanceOf(lp_token_staker)
#     assert before_stake_lp_balance - after_stake_lp_balance  == staking_amount
#     chain.mine(500)
#   ###########################
#   # Staker accounts[4]
#   ###########################
#     staking_amount = 50 * TENPOW18
#     lp_token_staker = accounts[4]
#     lp_token.approve(lp_staking,staking_amount,{"from":lp_token_staker})
#     before_stake_lp_balance = lp_token.balanceOf(lp_token_staker)
#     lp_staking.stakeAll({"from":lp_token_staker})
#     after_stake_lp_balance = lp_token.balanceOf(lp_token_staker)
#     assert before_stake_lp_balance - after_stake_lp_balance  == staking_amount
    

#     lp_token_staker = accounts[4]
#     chain.mine(499)
#     unstaking_amount = 50* TENPOW18
#     before_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)
#     tx = lp_staking.unstake(unstaking_amount, {"from":lp_token_staker})
#     after_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)
#   #  assert after_stake_rewards_balance -  before_stake_rewards_balance == (math.floor(500/25) + math.floor(500/75)) * 50

#     lp_token_staker = accounts[5]
#     unstaking_amount = 25* TENPOW18
#     before_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)
#     tx = lp_staking.unstake(unstaking_amount, {"from":lp_token_staker})
#     after_stake_rewards_balance = gaze_coin.balanceOf(lp_token_staker)
#    # assert after_stake_rewards_balance -  before_stake_rewards_balance == (math.floor(500/25) + math.floor(500/75)) * 25

# def test_lp_staking_limited_rewards(lp_token,lp_staking_limited_rewards,gaze_coin):
#     lp_token_staker = accounts[5]
#     staking_amount = 50* TENPOW18
#     lp_token.approve(lp_staking_limited_rewards,staking_amount,{"from":lp_token_staker})
#     before_stake_lp_balance = lp_token.balanceOf(lp_token_staker)
#     lp_staking_limited_rewards.stake(staking_amount, {"from":lp_token_staker})
#     after_stake_lp_balance = lp_token.balanceOf(lp_token_staker)
#     assert before_stake_lp_balance - after_stake_lp_balance  == staking_amount
    
    
#     chain.mine(1000)

#     unstaking_amount = 25* TENPOW18
#     print(lp_staking_limited_rewards.balanceOfGazeCoin())
#     #with reverts("GazeRewards.accumulatedLPRewards: No rewards to distribute"):
#     tx = lp_staking_limited_rewards.unstake(unstaking_amount, {"from":lp_token_staker})
#     print(lp_staking_limited_rewards.balanceOfGazeCoin())
#     with reverts("GazeRewards.accumulatedLPRewards: No rewards to distribute"):
#       tx = lp_staking_limited_rewards.unstake(unstaking_amount, {"from":lp_token_staker})
# #########################
# # Helper Function
# #########################
# @pytest.fixture(scope='function',autouse = True)
# def lp_staking_limited_rewards(rewards_contract):


#     gaze_coin.approve(lp_staking_limited_rewards,500 ,{'from':accounts[1]})
    
    
#     assert gaze_coin.balanceOf(lp_staking_limited_rewards) == 500
#     lp_staking_limited_rewards.initLPStaking(gaze_coin,lp_token,weth_token,access_control,{"from":accounts[0]})

#     lp_staking_limited_rewards.setTokensClaimable(True,{"from":accounts[0]})
    
#     return lp_staking_limited_rewards 

# @pytest.fixture(scope = 'function', autouse = True)
# def rewards_contract_limited_rewards(GazeRewards,gaze_coin, access_control,lp_staking_limited_rewards):

#     rewards_contract_limited_rewards = GazeRewards.deploy(gaze_coin,
#                                         access_control,
#                                         lp_staking_limited_rewards,
#                                         chain.time() +10,
#                                         0,
#                                         0,
#                                         {'from': accounts[0]})
#     lp_staking_limited_rewards.setRewardsContract(rewards_contract_limited_rewards,{"from":accounts[0]})
#     return rewards_contract_limited_rewards
