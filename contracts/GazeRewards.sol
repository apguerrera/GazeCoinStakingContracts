pragma solidity ^0.6.12;

import "@openzeppelin/contracts/math/SafeMath.sol";
import "./Utils/GazeAccessControls.sol";

interface GazeStaking {
        function lpToken() external view returns (address);
        function WETH() external view returns (address);
    }

contract GazeRewards {
    using SafeMath for uint256;

    /// @notice Contract GazeAccessControls.
    GazeAccessControls public accessControls;

    /// @notice Block number when bonus ends.
    uint256 public LPBonusEndBlock;

    ///@notice Bonus multiplier constant.
    uint256 public LPBonusMultiplier;

    /// @dev GazeStaking lpStaking;

    constructor(GazeAccessControls _accessControls) public {
        accessControls = _accessControls;
    }

    /**
     * @notice Admin can set bonus variables.
     * @param _bonusEndBlock Number of the bonus end block.
     * @param _bonusMultiplier Number of the bonus multiplier.
     */
    function setLPBonus(uint256 _bonusEndBlock, uint256 _bonusMultiplier) external {
        require(accessControls.hasAdminRole(msg.sender), "GazeLPStaking.setLPBonus: Sender must be admin");
        LPBonusEndBlock = _bonusEndBlock;
        LPBonusMultiplier = _bonusMultiplier;
    }

    /**
     * @notice Displays number of LP rewards between 2 block timestamps.
     * @param _from Starting block number.
     * @param _to Ending block number.
     * @return Number of LP rewards.
     */
    function LPRewards(uint256 _from, uint256 _to) external view returns (uint256 rewards) {
        if (_to <= LPBonusEndBlock) {
            return _to.sub(_from).mul(LPBonusMultiplier);
        } else if (_from >= LPBonusEndBlock) {
            return _to.sub(_from);
        } else {
            return LPBonusEndBlock.sub(_from).mul(LPBonusMultiplier).add(_to.sub(LPBonusEndBlock));
            }
        }
}
