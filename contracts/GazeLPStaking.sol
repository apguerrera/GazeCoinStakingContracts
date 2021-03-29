pragma solidity ^0.6.12;

import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "../interfaces/IWETH9.sol";
import "../interfaces/IGazeRewards.sol";
import "./Utils/GazeAccessControls.sol";


contract GazeLPStaking {
    using SafeMath for uint256;
    using SafeERC20 for IERC20;

    /// @notice Reward token for LP staking.
    IERC20 public rewardsToken;

    /// @notice LP token to stake.
    address public lpToken;

    /// @notice WETH token.
    IWETH public WETH;

    /// @notice The sum of all the LP tokens staked.
    uint256 public stakedLPTotal;

    /// @notice The sum of all the unclaimed reward tokens.
    uint256 public totalUnclaimedRewards;

    //uint256 lpAllocPoint;

    /// @notice The latest block where rewards were distributed.
    uint256 lastRewardBlock;

    /// @notice Rewards accumulated per one LP token.
    uint256 accRewardsPerToken;

    /// @notice Block number when the bonus ends.
    uint256 public bonusEndBlock;

    /// @notice Reward tokens created per block.
    uint256 public rewardsPerBlock;

    /// @notice Bonus muliplier for early rewards makers.
    uint256 public bonusMultiplier;

    /// @notice IGazeRewards contract interface.
    IGazeRewards public rewardsContract;

    /// @notice Constant multiplier.
    uint256 constant pointMultiplier = 10e32;

    /// @notice Start block of the LP staking.
    uint256 public startBlock;

    /// @notice Contract GazeAccessControls.
    GazeAccessControls public accessControls;

    /// @notice Staker information.
    struct Staker {
        uint256 balance;
        uint256 rewardDebt;
    }

    /// @notice Mapping from staker address to its current info.
    mapping (address => Staker) public stakers;

    /// @notice Mapping from token ID to its owner address.
    mapping (uint256 => address) public tokenOwner;

    /// @notice Sets the token to be claimable or not (cannot claim if it set to false).
    bool public tokensClaimable;

    /// @notice Whether staking has been initialised or not.
    bool private initialised;

    /**
     * @notice Event emmited when a user has staked LPs.
     * @param owner Address of the staker.
     * @param amount Amount staked in LP tokens.
     */
    event Staked(address indexed owner, uint256 amount);

    /**
     * @notice Event emitted when a user has unstaked LPs.
     * @param owner Address of the unstaker.
     * @param amount Amount unstaked in LP tokens.
     */
    event Unstaked(address indexed owner, uint256 amount);

    /**
     * @notice Event emitted when a user claims rewards.
     * @param user Address of the user.
     * @param reward Reward amount.
     */
    event RewardPaid(address indexed user, uint256 reward);

    /**
     * @notice Event emitted when claimable status is updated.
     * @param status True or False.
     */
    event ClaimableStatusUpdated(bool status);

    /**
     * @notice Event emitted when user unstaked in emergency mode.
     * @param user Address of the user.
     * @param amount Amount unstaked in LP tokens.
     */
    event EmergencyUnstake(address indexed user, uint256 amount);

    /**
     * @notice Event emitted when rewards contract has been updated.
     * @param oldRewardsToken Address of the old reward token contract.
     * @param newRewardsToken Address of the new reward token contract.
     */
    event RewardsContractUpdated(address indexed oldRewardsToken, address newRewardsToken);

    /**
     * @notice Event emitted when LP token has been updated.
     * @param oldRewardsToken Address of the old LP token contract.
     * @param newRewardsToken Address of the new LP token contract.
     */
    event LpTokenUpdated(address indexed oldLpToken, address newLpToken);

    /**
     * @notice Event emitted when the number of rewards per block is updated.
     * @param rewardsPerBlock Number of rewards per block.
     */
    event RewardsPerBlockUpdated(uint256 rewardsPerBlock);

    constructor() public{

    }

    /**
     * @notice Initializes main contract variables.
     * @dev Init function.
     * @param _rewardsToken Reward token interface.
     * @param _lpToken Address of the LP token.
     * @param _WETH Wrapped Ether interface.
     * @param _rewardsPerBlock Number of rewards token allocated per block.
     * @param _accessControls Access controls interface.
     * @param _startBlock Number of the block when LP staking starts.
     */
    function initLPStaking(
        IERC20 _rewardsToken,
        address _lpToken,
        IWETH _WETH,
        uint256 _rewardsPerBlock,
        GazeAccessControls _accessControls,
        uint256 _startBlock
    ) public {
        require(!initialised, "Already initialised");
        rewardsToken = _rewardsToken;
        lpToken = _lpToken;
        WETH = _WETH;
        rewardsPerBlock = _rewardsPerBlock;
        /// @dev Check Last Rewards Block.
        accessControls = _accessControls;
        startBlock = _startBlock;
        accRewardsPerToken = 0;
        lastRewardBlock = block.number > _startBlock ? block.number : _startBlock;
        initialised = true;
    }

    /**
     * @notice Admin can change rewards contract through this function.
     * @param _addr Address of the new rewards contract.
     */
    function setRewardsContract(address _addr) external {
        require(accessControls.hasAdminRole(msg.sender), "GazeLPStaking.setRewardsContract: Sender must be admin");
        require(_addr != address(0));
        address oldAddr = address(rewardsContract);
        rewardsContract = IGazeRewards(_addr);
        emit RewardsContractUpdated(oldAddr, _addr);
    }

    /**
     * @notice Admin can change LP token through this function.
     * @param _addr Address of the new LP token contract.
     */
    function setLPToken(address _addr) external {
        require(accessControls.hasAdminRole(msg.sender), "GazeLPStaking.setLPToken: Sender must be admin");
        require(_addr != address(0));
        address oldAddr = lpToken;
        lpToken = _addr;
        emit LpTokenUpdated(oldAddr, _addr);
    }

    /**
     * @notice Admin can set reward tokens claimable through this function.
     * @param _enabled True or False.
     */
    function setTokensClaimable(bool _enabled) external {
        require(accessControls.hasAdminRole(msg.sender), "GazeLPStaking.setTokensClaimable: Sender must be admin");
        tokensClaimable = _enabled;
        emit ClaimableStatusUpdated(_enabled);
    }

    /**
     * @notice Admin can change the number of rewards per block through this function.
     * @param _rewardsPerBlock Number of rewards per block.
     */
    function setRewardsPerBlock(uint256 _rewardsPerBlock) external {
        require(accessControls.hasAdminRole(msg.sender), "GazeLPStaking.setRewardsPerBlock: Sender must be admin");
        rewardsPerBlock = _rewardsPerBlock;
        emit RewardsPerBlockUpdated(_rewardsPerBlock);
    }

    /**
     * @notice Function to retrieve balance of LP tokens staked by a user.
     * @param _user User address.
     * @return Number of LP tokens staked.
     */
    function getStakedBalance(address _user) external view returns (uint256 balance) {
        return stakers[_user].balance;
    }

    /**
     * @notice Function for staking exact amount of LP tokens.
     * @param _amount Number of LP tokens.
     */
    function stake(uint256 _amount) external {
        _stake(msg.sender, _amount);
    }

    /// @notice Function for staking all of users LP tokens.
    function stakeAll() external {
        uint256 balance = IERC20(lpToken).balanceOf(msg.sender);
        _stake(msg.sender, balance);
    }

    /**
     * @notice Function that executes the staking.
     * @param _user Stakers address.
     * @param _amount Number of LP tokens to stake.
     */
    function _stake(address _user, uint256 _amount) internal {
        require(_amount > 0, "GazeLPStaking._stake: Staked amount must be greater than 0");
        updateRewardPool(_user);
        Staker storage staker = stakers[_user];
        // CC Redundant if statement? (beacuase the same condition in require above)
        if (_amount > 0) {
            staker.balance = staker.balance.add(_amount);
            stakedLPTotal = stakedLPTotal.add(_amount);
            IERC20(lpToken).safeTransferFrom(address(_user), address(this), _amount);
        }
        emit Staked(_user, _amount);
    }

    /**
     * @notice Function for unstaking exact amount of LP tokens.
     * @param _amount Number of LP tokens.
     */
    function unstake(uint256 _amount) external {
        _unstake(msg.sender, _amount);
    }

    // CC Either unstakeAll is missing or the unstake and _unstake could be merged into one function?

    /**
     * @notice Function that executes the unstaking.
     * @param _user Stakers address.
     * @param _amount Number of LP tokens to unstake.
     */
    function _unstake(address _user, uint256 _amount) internal {
        Staker storage staker = stakers[_user];
        // CC Maybe require message better formulated?
        // CC In the require statement isn't staker.balance better?
        require(stakers[_user].balance >= _amount, "withdraw: not good");
        claimRewards(_user);

        if (_amount > 0) {
             staker.balance = staker.balance.sub(_amount);
             stakedLPTotal = stakedLPTotal.sub(_amount);
        }

        if (staker.balance == 0) {
            delete stakers[_user];
        }

        uint256 tokenBal = IERC20(lpToken).balanceOf(address(this));

        if (_amount > tokenBal) {
            IERC20(lpToken).safeTransfer(address(_user), tokenBal);
        } else {
            IERC20(lpToken).safeTransfer(address(_user), _amount);
        }

        staker.rewardDebt = totalRewardsOwing(_user);
        emit Unstaked(_user, _amount);
    }

    /**
     * @notice Updates reward pool.
     * @param _user User address.
     */
    // CC Is the _user parameter acctually needed?
    function updateRewardPool(address _user) public {
        if (block.number <= lastRewardBlock) {
            return;
        }

        uint256 lpSupply = IERC20(lpToken).balanceOf(address(this));

        if (lpSupply == 0) {
            lastRewardBlock = block.number;
            return;
        }

        uint256 lpRewards = rewardsContract.LPRewards(lastRewardBlock, block.number);
        uint256 rewardsAccum = lpRewards.mul(rewardsPerBlock);
        accRewardsPerToken = accRewardsPerToken.add(rewardsAccum.mul(1e18).div(lpSupply));
        lastRewardBlock = block.number;

       /*  if (devPercentage > 0) {
            tips = tips.add(rewardsAccum.mul(devPercentage).div(1000));
        } */
    }

    /**
     * @notice Claiming rewards for user.
     * @param _user User address.
     */
    function claimRewards(address _user) public {
        updateRewardPool(_user);
        uint256 pending = totalRewardsOwing(_user).sub(stakers[_user].rewardDebt);

        if (pending > 0) {
            require(tokensClaimable == true, "Tokens cannnot be claimed yet");
            safeRewardsTransfer(msg.sender, pending);
        }
    }

    /// @notice Emergency unstaking of all of users LP tokens without any rewards.
    function emergencyUnstake() external {
        Staker storage staker = stakers[msg.sender];
        uint256 amount = staker.balance;
        staker.balance = 0;
        staker.rewardDebt = 0;
        uint256 tokenBal = IERC20(lpToken).balanceOf(address(this));

        if (amount > tokenBal) {
            IERC20(lpToken).safeTransfer(address(msg.sender), tokenBal);
        } else {
            IERC20(lpToken).safeTransfer(address(msg.sender), amount);
        }
    }

    /**
     * @notice Rewards owing to the user.
     * @param _user User address.
     * @return Number of rewards.
     */
    function totalRewardsOwing(address _user) public returns (uint256) {
        uint256 rewards =  stakers[_user].balance.mul(accRewardsPerToken).div(1e18);
        return rewards;
    }

    /**
     * @notice Rewards transfer to the user.
     * @param _to User address.
     * @param _amount Number of rewards.
     */
    function safeRewardsTransfer(address _to, uint256 _amount) internal {
        uint256 rewardsBal = rewardsToken.balanceOf(address(this));

        if (_amount > rewardsBal) {
            IERC20(rewardsToken).safeTransfer(_to, rewardsBal);
        } else {
            IERC20(rewardsToken).safeTransfer(_to, _amount);
        }
    }

    /**
     * @notice Returns the number of blocks remaining with rewards available.
     * @return Number of blocks.
     */
    function blocksRemaining() public returns (uint256){
        uint256 rewardsBal = rewardsToken.balanceOf(address(this));
        if (rewardsPerBlock > 0) {
            return rewardsBal / rewardsPerBlock;
        } else {
            return 0;
        }
    }
}
