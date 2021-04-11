from brownie import *
from .settings import *
from .contracts import *
from .contract_addresses import *
import time

def verify(contract_id, container):
    contract_address = CONTRACTS[network.show_active()][contract_id]
    contract = container.at(contract_address)
    print(contract_id, ": Verification initiated..")
    try:
        container.publish_source(contract)
        # print(container.get_verification_info())
    except:
        print(contract_id, ": Already verified")

def main():

    verify("access_control", GazeAccessControls)
    verify("gaze_coin", BTTSToken) 
    verify("weth", WETH9) 
    verify("lp_token", UniswapV2Pair) 
    verify("rewards_contract", GazeRewards) 
    verify("lp_staking", GazeLPStaking) 
    verify("btts_lib", BTTSLib) 
