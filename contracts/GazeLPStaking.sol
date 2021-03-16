pragma solidity ^0.6.12;

import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "../interfaces/IWETH9.sol";
import "../interfaces/IGazeRewards.sol";
import "./Utils/GazeAccessControls.sol";


contract GazeLPStaking{
    using SafeMath for uint256;
    using SafeERC20 for IERC20;


    IERC20 public rewardsToken;
    address public lpToken;
    IWETH public WETH;

/// SSS: CHECK THIS OUT
    uint256 public stakedLPTotal;
    uint256 public totalUnclaimedRewards;
    
    //uint256 lpAllocPoint;
    uint256 lastRewardBlock;
    uint256 accRewardsPerToken;


    uint256 public bonusEndBlock;
    // Reward tokens created per block.
    uint256 public rewardsPerBlock;
    // Bonus muliplier for early rewards makers.
    uint256 public bonusMultiplier;

    IGazeRewards public rewardsContract;

    uint256 constant pointMultiplier = 10e32;
    
    GazeAccessControls public accessControls;
    struct Staker {
        uint256 balance;
        uint256 rewardsReleased;
        uint256 rewardDebt;
    }

    /// @notice mapping of a staker to its current properties
    mapping (address => Staker) public stakers;

    // Mapping from token ID to owner address
    mapping (uint256 => address) public tokenOwner;

    /// @notice sets the token to be claimable or not, cannot claim if it set to false
    bool public tokensClaimable;
    bool private initialised;


    event Staked(address indexed owner, uint256 amount);

    /// @notice event emitted when a user has unstaked a token
    event Unstaked(address indexed owner, uint256 amount);

    /// @notice event emitted when a user claims reward
    event RewardPaid(address indexed user, uint256 reward);
    
    event ClaimableStatusUpdated(bool status);
    event EmergencyUnstake(address indexed user, uint256 amount);
    event RewardsContractUpdated(address indexed oldRewardsToken, address newRewardsToken );
    event LpTokenUpdated(address indexed oldLpToken, address newLpToken );
    
    event RewardsPerBlockUpdated(uint256 rewardsPerBlock);

    constructor() public{

    }

    function initLPStaking(
        IERC20 _rewardsToken,
        address _lpToken,
        IWETH _WETH,
        uint256 _rewardsPerBlock,
        GazeAccessControls _accessControls
    ) public 
    {
        require(!initialised, "Already initialised");
        rewardsToken = _rewardsToken;
        lpToken = _lpToken;
        WETH = _WETH;
        rewardsPerBlock = _rewardsPerBlock;
        //check Last Rewards Block
        accessControls = _accessControls;
        lastRewardBlock = block.number;
        accRewardsPerToken = 0;
        
        initialised = true;
    }
    
    function setRewardsContract(
        address _addr
    ) external{
        require(
            accessControls.hasAdminRole(msg.sender),
            "GazeLPStaking.setRewardsContract: Sender must be admin"
        );
        require(_addr != address(0));
        address oldAddr = address(rewardsContract);
        rewardsContract = IGazeRewards(_addr);
        emit RewardsContractUpdated(oldAddr, _addr);
    }

    //Implement Access Control
    function setLPToken(address _addr) 
        external 
    {   

        require(
            accessControls.hasAdminRole(msg.sender),
            "GazeLPStaking.setLPToken: Sender must be admin"
        );
        require(_addr != address(0));
        address oldAddr = lpToken;
        lpToken = _addr;
        emit LpTokenUpdated(oldAddr, _addr);
    }

   
       //Implement Access Control
    function setTokensClaimable(bool _enabled)
        external
    {
        require(
            accessControls.hasAdminRole(msg.sender),
            "GazeLPStaking.setTokensClaimable: Sender must be admin"
        );
        tokensClaimable = _enabled;
        emit ClaimableStatusUpdated(_enabled);
    }

    
    function setRewardsPerBlock(uint256 _rewardsPerBlock) external{
         require(
            accessControls.hasAdminRole(msg.sender),
            "GazeLPStaking.setRewardsPerBlock: Sender must be admin"
        );
        rewardsPerBlock = _rewardsPerBlock;
        emit RewardsPerBlockUpdated(_rewardsPerBlock);
    }


    function getStakedBalance(address _user) 
        external view 
            returns(uint256 balance)
    {
            return stakers[_user].balance;
    }

    function stake(uint256 _amount) 
        external
    {
            _stake(msg.sender, _amount);
    }
                
    function stakeAll()
        external
    {
            uint256 balance = IERC20(lpToken).balanceOf(msg.sender);
            _stake(msg.sender, balance);
    }

    function _stake(
        address _user,
        uint256 _amount
    )
        internal
    {
        require(
            _amount > 0,
            "GazeLPStaking._stake: Staked amount must be greater than 0"
        );
        Staker storage staker = stakers[_user];
        updateRewardPool(_user);


        if(_amount > 0){
            staker.balance = staker.balance.add(_amount);
            stakedLPTotal = stakedLPTotal.add(_amount);

            IERC20(lpToken).safeTransferFrom(
                address(_user),
                address(this),
                _amount
            );
        }

        emit Staked(_user, _amount);


    }



    function unstake(uint256 _amount) external{
            
            _unstake(msg.sender, _amount);
            
    }


    function _unstake(address _user, uint256 _amount) internal{
        Staker storage staker = stakers[_user];
        require(staker.balance >= _amount, "withdraw: not good");
        updateRewardPool(_user);
        uint256 pending = staker.balance.mul(accRewardsPerToken).div(1e18).sub(staker.rewardDebt);

        if(pending > 0) {
            require(tokensClaimable == true,"Tokens cannnot be claimed yet");
            
            safeRewardsTransfer(msg.sender, pending);
        }

        
        if(_amount>0){
             staker.balance = staker.balance.sub(_amount);
             stakedLPTotal = stakedLPTotal.sub(_amount);
        }
        if (staker.balance == 0) {
            delete stakers[_user];
        }
        uint256 tokenBal = IERC20(lpToken).balanceOf(address(this));

        if(_amount > tokenBal){
            IERC20(lpToken).safeTransfer(address(_user), tokenBal);
        }else {
            IERC20(lpToken).safeTransfer(address(_user), _amount);
        }

        staker.rewardDebt = totalRewardsOwing(_user);
        emit Unstaked(_user, _amount);
    }

    function updateRewardPool(address _user)
        public
    {
        if (block.number <= lastRewardBlock){
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

    function totalRewardsOwing(address _user)
        public
        view
        returns(uint256)
    {   

        uint256 rewards = stakers[_user].balance.mul(accRewardsPerToken).div(1e18);
    }

    
    ///Accounts for dust
    function safeRewardsTransfer(address _to, uint256 _amount) internal {
        uint256 rewardsBal = rewardsToken.balanceOf(address(this));
        if (_amount > rewardsBal) {
            IERC20(rewardsToken).safeTransfer(
                _to,
                rewardsBal
            );
        } else {
              IERC20(rewardsToken).safeTransfer(
                _to,
                _amount
            );
        }
    }


} 