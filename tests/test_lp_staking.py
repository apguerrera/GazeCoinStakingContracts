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


def test_lp_staking(lp_token,gaze_stake_lp,gaze_coin):
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
