pragma solidity ^0.6.12;

import "@openzeppelin/contracts/math/SafeMath.sol";
import "./Utils/GazeAccessControls.sol";


interface GazeStaking{
        function lpToken() external view returns (address);
        function WETH() external view returns (address);
    }

contract GazeRewards {
    using SafeMath for uint256;
    GazeAccessControls public accessControls;

    uint256 public LPBonusEndBlock;
    uint256 public LPBonusMultiplier;
    uint256 public LPRewardsPerBlock;

    event LPBonusSet(uint256 bonusEndBlock,uint256 bonusMultiplier);
    event RewardsPerBlockUpdated(uint256 oldRewardsPerBlock, uint256 rewardsPerBlock);
    constructor(
        GazeAccessControls _accessControls,
        uint256 _LPRewardsPerBlock
    ) public {
        accessControls = _accessControls;
        LPRewardsPerBlock = _LPRewardsPerBlock;
    }

    function setLPRewardsPerBlock(
        uint256 
        _LPRewardsPerBlock
        ) external{
         require(
            accessControls.hasAdminRole(msg.sender),
            "GazeRewards.setLPRewardsPerBlock: Sender must be admin"
        );
        uint256 oldLPRewardsPerBlock = LPRewardsPerBlock;
        LPRewardsPerBlock = _LPRewardsPerBlock;
        emit RewardsPerBlockUpdated(oldLPRewardsPerBlock,_LPRewardsPerBlock);
    }

    function setLPBonus(
        uint256 _bonusEndBlock,
        uint256 _bonusMultiplier
    ) external{
        require(
            accessControls.hasAdminRole(msg.sender),
            "GazeRewards.setLPBonus: Sender must be admin"
        );

        LPBonusEndBlock = _bonusEndBlock;
        LPBonusMultiplier = _bonusMultiplier;
        emit LPBonusSet(_bonusEndBlock,_bonusMultiplier);
    }


    function LPRewards(uint256 _from, uint256 _to) 
        internal 
        view 
        returns (uint256 rewards){
        if (_to <= LPBonusEndBlock) {
                return _to.sub(_from).mul(LPBonusMultiplier);
            } else if (_from >= LPBonusEndBlock) {
                return _to.sub(_from);
            } else {
                return LPBonusEndBlock.sub(_from).mul(LPBonusMultiplier).add(
                    _to.sub(LPBonusEndBlock)
                );
            }
        }

    function accumulatedLPRewards(uint256 _from, uint256 _to)
        external 
        view 
        returns (uint256 rewardsAccumulated)
    {
        uint256 lpRewards = LPRewards(_from, _to);
        rewardsAccumulated = lpRewards.mul(LPRewardsPerBlock);
    } 

}