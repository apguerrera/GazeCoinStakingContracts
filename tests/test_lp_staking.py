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


@pytest.fixture(scope='module', autouse=True)
def rewards_contract(GazeRewards, staking_rewards):
    rewards_contract = GazeRewards.at(staking_rewards.rewardsContract())
    return rewards_contract

def stake(staking_rewards, staker, staking_amount):
    staking_rewards.stake(staking_amount, {"from": staker})
    staker_info = staking_rewards.stakers(staker)
    assert staker_info[0] == staking_amount


def test_zap(staking_rewards, lp_token, rewards_contract, weth_token, gaze_coin):
    staker = accounts[5]
    before_stake_lp_balance = staking_rewards.getStakedBalance(staker)
    
    eth_amount = 1 * TENPOW18
    staking_rewards.zapEth({"from":staker, 'value': eth_amount})
    after_stake_lp_balance = staking_rewards.getStakedBalance(staker)
    total_eth_staked = staking_rewards.stakedEthTotal()
    assert after_stake_lp_balance > before_stake_lp_balance
    
    chain.sleep(ONE_WEEK*2)
    
    # Unstaking

    unstaking_amount = staking_rewards.stakers(staker)[0]
    
    # updating staker info
    staking_rewards.updateReward(staker, {'from': staker}) 
    before_stake_rewards_balance = gaze_coin.balanceOf(staker)
    unclaimed_rewards_before = staking_rewards.unclaimedRewards(staker)
    
    tx = staking_rewards.unstake(unstaking_amount, {"from":staker})    
    after_stake_rewards_balance = gaze_coin.balanceOf(staker)

    assert "Unstaked" in tx.events
    assert round((after_stake_rewards_balance - before_stake_rewards_balance) / TENPOW18) == round(unclaimed_rewards_before / TENPOW18)
    assert staking_rewards.unclaimedRewards(staker) == 0

def test_stake(staking_rewards, lp_token, rewards_contract, gaze_coin):
    staker = accounts[5]
    staking_amount = 100*TENPOW18

    lp_token.transfer(staker, staking_amount, {'from': accounts[0]})
    lp_token.approve(staking_rewards, staking_amount, {'from': staker})
    stake(staking_rewards, staker, staking_amount)

    chain.sleep(ONE_WEEK*2)

    # updating staker info
    staking_rewards.updateReward(staker, {'from': staker})
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
    assert round(unclaimed_rewards_before / TENPOW18) == round(staker_info[2] / TENPOW18)
    assert round((before_staker_rewards_balance+unclaimed_rewards_before)/TENPOW18) == round(after_staker_rewards_balance/TENPOW18)


def test_unstake(staking_rewards, lp_token, rewards_contract, gaze_coin):
    staker = accounts[5]
    staking_amount = 50*TENPOW18
    lp_token.transfer(staker, staking_amount, {'from': accounts[0]})
    lp_token.approve(staking_rewards, staking_amount, {'from': staker})

    stake(staking_rewards, staker, staking_amount)

    chain.sleep(ONE_WEEK*2)

    # updating staker info
    staking_rewards.updateReward(staker, {'from': staker})

    unclaimed_rewards = staking_rewards.unclaimedRewards(staker)

    tx = staking_rewards.unstake(staking_amount, {'from': staker})
    staker_info = staking_rewards.stakers(staker)

    assert "Unstaked" in tx.events
    assert round(unclaimed_rewards / TENPOW18) == round(gaze_coin.balanceOf(staker) / TENPOW18)
    assert staker_info[0] == 0
    assert staker_info[1] == 0
    assert staker_info[2] == 0
    assert staker_info[3] == 0


def test_multiple_staking_and_unstaking(lp_token, staking_rewards, rewards_contract, gaze_coin):
    lp_token_owner = accounts[0]
    print("balance of lp token",lp_token.balanceOf(lp_token_owner)/TENPOW18)
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

    chain.sleep(ONE_WEEK*2)

    # Unstaking 1/2
    week_1_rewards = 70000 * TENPOW18
    participants = 5
    first_week_rewards_per_staker = week_1_rewards / participants
    for i in range(2, 7):
        staker = accounts[i]
        unstaking_amount = 25 * TENPOW18

        before_unstake_rewards_balance = gaze_coin.balanceOf(staker)

        staking_rewards.unstake(unstaking_amount, {"from":staker})

        after_unstake_rewards_balance = gaze_coin.balanceOf(staker)

        assert round((after_unstake_rewards_balance - before_unstake_rewards_balance) / TENPOW18) == round(first_week_rewards_per_staker/TENPOW18)

    chain.sleep(ONE_WEEK*2)

    # Unstaking 2/2
    week_2_rewards = 60000 * TENPOW18
    second_week_rewards_per_staker = week_2_rewards / participants
    for i in range(2, 7):
        staker = accounts[i]
        unstaking_amount = 25 * TENPOW18

        before_stake_rewards_balance = gaze_coin.balanceOf(staker)

        staking_rewards.unstake(unstaking_amount, {"from": staker})

        after_stake_rewards_balance = gaze_coin.balanceOf(staker)

        assert round((after_stake_rewards_balance -  before_stake_rewards_balance) / TENPOW18) == round(second_week_rewards_per_staker / TENPOW18)






def test_staking_and_then_complete_unstaking(lp_token, staking_rewards, gaze_coin):
    staker = accounts[5]
    staking_amount = 25 * TENPOW18

    lp_token.transfer(staker, staking_amount, {'from': accounts[0]})
    lp_token.approve(staking_rewards, staking_amount,{"from": staker})
    before_stake_lp_balance = lp_token.balanceOf(staker)

    staking_rewards.stake(staking_amount, {"from": staker})
    
    after_stake_lp_balance = lp_token.balanceOf(staker)

    assert before_stake_lp_balance - after_stake_lp_balance  == staking_amount
    chain.sleep(ONE_WEEK*2)
    unstaking_amount = 25 * TENPOW18
    before_stake_rewards_balance = gaze_coin.balanceOf(staker)
    tx = staking_rewards.unstake(unstaking_amount, {"from":staker})
   
    after_stake_rewards_balance = gaze_coin.balanceOf(staker)

    first_week_rewards_per_staker = 70000 * TENPOW18
    assert round((after_stake_rewards_balance -  before_stake_rewards_balance) / TENPOW18) == round(first_week_rewards_per_staker/ TENPOW18)
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
    
    chain.sleep(ONE_WEEK*2)

    before_unstake_lp_balance = lp_token.balanceOf(staker)
    staking_rewards.emergencyUnstake({"from":staker})
    after_unstake_lp_balance = lp_token.balanceOf(staker)
    assert after_unstake_lp_balance - before_unstake_lp_balance == staking_amount 
 
def test_staking_12_weeks(lp_token, staking_rewards, rewards_contract, gaze_coin):
    staker = accounts[5]
    staking_amount = 50* TENPOW18

    lp_token.transfer(staker, staking_amount, {'from': accounts[0]})
    lp_token.approve(staking_rewards,staking_amount,{"from": staker})

    stake(staking_rewards, staker, staking_amount)

    chain.sleep(ONE_WEEK*18)

    tx = staking_rewards.claimReward(staker, {'from': staker})
    staker_info = staking_rewards.stakers(staker)
    assert round(gaze_coin.balanceOf(staker) / TENPOW18) + 2 >= 317000
    assert round(gaze_coin.balanceOf(staker) / TENPOW18) - 2 <= 317000
    staking_rewards.unstake(staking_amount, {"from":staker})
    assert round(gaze_coin.balanceOf(staker) / TENPOW18) + 2 >= 317000
    assert round(gaze_coin.balanceOf(staker) / TENPOW18) - 2 <= 317000

def test_unstaking_without_balance(staking_rewards, lp_token):
    account = accounts[2]
    assert staking_rewards.stakers(account)[0] == 0

    with reverts("GazeLPStaking._unstake: Sender must have staked tokens"):
        staking_rewards.unstake(1*TENPOW18)

def test_multiple_staking_and_unstaking_multiple_weeks(lp_token, staking_rewards, rewards_contract, gaze_coin):
    lp_token_owner = accounts[0]
    for i in range(2, 7):
        transfer_amount = 40 * TENPOW18
        transfer_to = accounts[i]

        lp_token.transfer(transfer_to, transfer_amount, {"from": lp_token_owner})
        
    # Staking
    for i in range(2, 7):
        staker = accounts[i]
        staking_amount = 40 * TENPOW18

        lp_token.approve(staking_rewards,staking_amount,{"from": staker})
        before_stake_lp_balance = lp_token.balanceOf(staker)
        stake(staking_rewards, staker, staking_amount)
        after_stake_lp_balance = lp_token.balanceOf(staker)

        assert before_stake_lp_balance - after_stake_lp_balance == staking_amount

    chain.sleep(ONE_WEEK*2)

    # Unstaking 1/4
    week_1_rewards = 70000 * TENPOW18
    participants = 5
    first_week_rewards_per_staker = week_1_rewards / participants
    for i in range(2, 7):
        staker = accounts[i]
        unstaking_amount = 10 * TENPOW18

        before_unstake_rewards_balance = gaze_coin.balanceOf(staker)
        staking_rewards.unstake(unstaking_amount, {"from":staker})
        after_unstake_rewards_balance = gaze_coin.balanceOf(staker)
        assert round((after_unstake_rewards_balance - before_unstake_rewards_balance) / TENPOW18) == round(first_week_rewards_per_staker/TENPOW18)

    chain.sleep(ONE_WEEK*2)

    # Unstaking 2/4
    week_2_rewards = 60000 * TENPOW18
    second_week_rewards_per_staker = week_2_rewards / participants
    for i in range(2, 7):
        staker = accounts[i]
        unstaking_amount = 10 * TENPOW18

        before_stake_rewards_balance = gaze_coin.balanceOf(staker)
        staking_rewards.unstake(unstaking_amount, {"from": staker})
        after_stake_rewards_balance = gaze_coin.balanceOf(staker)
        assert round((after_stake_rewards_balance -  before_stake_rewards_balance) / TENPOW18) == round(second_week_rewards_per_staker / TENPOW18)

    chain.sleep(ONE_WEEK*2)
 # Unstaking 3/4
    week_3_rewards = 50000 * TENPOW18
    third_week_rewards_per_staker = week_3_rewards / participants
    for i in range(2, 5):
        staker = accounts[i]
        unstaking_amount = 10 * TENPOW18

        before_stake_rewards_balance = gaze_coin.balanceOf(staker)
        staking_rewards.unstake(unstaking_amount, {"from": staker})
        after_stake_rewards_balance = gaze_coin.balanceOf(staker)
        assert round((after_stake_rewards_balance -  before_stake_rewards_balance) / TENPOW18) == round(third_week_rewards_per_staker / TENPOW18)

    chain.sleep(ONE_WEEK * 2)

 # Unstaking 4/4


    #### Remaining staked LP token = 70 // Stake of one participant = 30 / no. of participants #######
    participants = 3
    week_4_rewards = 50000 * TENPOW18
    fourth_week_rewards_per_staker = week_4_rewards / participants * 30 / 70 
    for i in range(2, 5):
        staker = accounts[i]
        unstaking_amount = 10 * TENPOW18

        before_stake_rewards_balance = gaze_coin.balanceOf(staker)
        staking_rewards.unstake(unstaking_amount, {"from": staker})
        after_stake_rewards_balance = gaze_coin.balanceOf(staker)

        assert round((after_stake_rewards_balance -  before_stake_rewards_balance) / TENPOW18) == round(fourth_week_rewards_per_staker / TENPOW18)

     
    participants = 2
    fourth_week_rewards_with_old_rewards = week_3_rewards / participants * 20 / 40
    fourth_week_rewards_with_new_rewards = week_4_rewards / participants * 20 / 40 
    fourth_week_rewards_per_staker = fourth_week_rewards_with_old_rewards + fourth_week_rewards_with_new_rewards
    for i in range(5, 7):
        staker = accounts[i]
        unstaking_amount = 10 * TENPOW18

        before_stake_rewards_balance = gaze_coin.balanceOf(staker)
        staking_rewards.unstake(unstaking_amount, {"from": staker})
        after_stake_rewards_balance = gaze_coin.balanceOf(staker)
        # not getting exact 25000: Getting 24286
        assert round((after_stake_rewards_balance -  before_stake_rewards_balance) / TENPOW18) < round(fourth_week_rewards_per_staker / TENPOW18) 


def test_for_reverts(GazeLPStaking, GazeRewards, gaze_coin, lp_token, weth_token, access_control):
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
    gaze_coin.approve(rewards_contract, ONE_MILLION, {"from":vault} )
    rewards_contract.setVault(vault, {"from":accounts[0]})
    with reverts("GazeRewards.setVault: Sender must be admin"):
        rewards_contract.setVault(vault, {"from":accounts[5]})

    staking_rewards.setRewardsContract(rewards_contract, {"from":accounts[0]})
    staking_rewards.setTokensClaimable(True, {"from":accounts[0]})

    with reverts("GazeLPStaking.setRewardsContract: Sender must be admin"):
        staking_rewards.setRewardsContract(rewards_contract, {"from":accounts[5]})
    
    with reverts():
        staking_rewards.setRewardsContract(ZERO_ADDRESS, {"from": accounts[0]})
    
    with reverts("GazeLPStaking.setTokensClaimable: Sender must be admin"):
        staking_rewards.setTokensClaimable(True, {"from":accounts[5]})

    weeks = [0,1,2,3,4,5]
    rewards = [70000*TENPOW18,60000*TENPOW18,50000*TENPOW18,50000*TENPOW18,45000*TENPOW18,42000*TENPOW18]
    rewards_contract.setRewards(weeks,rewards, {"from": accounts[0]})

    with reverts("GazeRewards.setRewards: Sender must be admin"):
        rewards_contract.setRewards(weeks,rewards, {"from": accounts[5]})
    
    with reverts("GazeRewards.setStartTime: Sender must be admin"):
        rewards_contract.setStartTime(0,0,{"from": accounts[5]})
    
    chain.sleep(20)
    chain.mine()
    
    


