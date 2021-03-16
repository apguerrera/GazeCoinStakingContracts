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

    GazeStaking lpStaking;

    constructor(
        GazeAccessControls _accessControls
    ) public {
        accessControls = _accessControls;
    }

    function setLPBonus(
        uint256 _bonusEndBlock,
        uint256 _bonusMultiplier
    ) external{
        require(
            accessControls.hasAdminRole(msg.sender),
            "GazeLPStaking.setLPBonus: Sender must be admin"
        );

        LPBonusEndBlock = _bonusEndBlock;
        LPBonusMultiplier = _bonusMultiplier;
    }


    function LPRewards(uint256 _from, uint256 _to) external view returns (uint256 rewards){
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
} 