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
    
    //uint256 lpAllocPoint;
    uint256 lastRewardBlock;
    uint256 accRewardsPerToken;

    IGazeRewards public rewardsContract;

    
    uint256 public startBlock;

    GazeAccessControls public accessControls;
    struct Staker {
        uint256 balance;
        uint256 rewardDebt;
    }

    /// @notice mapping of a staker to its current properties
    mapping (address => Staker) public stakers;

   

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

    function initLPStaking(
        IERC20 _rewardsToken,
        address _lpToken,
        IWETH _WETH,
        GazeAccessControls _accessControls,
        uint256 _startBlock
    ) public 
    {
        require(!initialised, "Already initialised");
        rewardsToken = _rewardsToken;
        lpToken = _lpToken;
        WETH = _WETH;
        //check Last Rewards Block
        accessControls = _accessControls;
        startBlock = _startBlock;
        accRewardsPerToken = 0;
        lastRewardBlock = block.number > _startBlock ? block.number : _startBlock;
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

    
  
    function getStakedBalance(
        address _user
    )
        external
        view
        returns (uint256 balance)
    {
        return stakers[_user].balance;
    }

    //for frontend
    function pendingRewards(address _user) 
        external 
        view
         
        returns(uint256){
            Staker storage staker = stakers[_user];
            uint256 lpSupply = IERC20(lpToken).balanceOf(address(this));
            uint256 accRewardsPerTokenHolder = accRewardsPerToken;
            if (block.number > lastRewardBlock && lpSupply != 0){
                uint256 rewardsAccum = rewardsContract.accumulatedLPRewards(lastRewardBlock, block.number);
                accRewardsPerTokenHolder = accRewardsPerToken.add(rewardsAccum.mul(1e18).div(lpSupply));
            }
            return staker.balance.mul(accRewardsPerTokenHolder).div(1e18).sub(staker.rewardDebt);
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
        updateRewardPool();
        Staker storage staker = stakers[_user];

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
        require(stakers[_user].balance >= _amount, "withdraw: not good");
        claimRewards(_user);
      
        staker.balance = staker.balance.sub(_amount);
        stakedLPTotal = stakedLPTotal.sub(_amount);
        
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

    function updateRewardPool()
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

        uint256 rewardsAccum = rewardsContract.accumulatedLPRewards(lastRewardBlock, block.number);
        accRewardsPerToken = accRewardsPerToken.add(rewardsAccum.mul(1e18).div(lpSupply));
        lastRewardBlock = block.number;

        
       /*  if (devPercentage > 0) {
            tips = tips.add(rewardsAccum.mul(devPercentage).div(1000));
        } */
        
    }
    function claimRewards(address _user) public{
        updateRewardPool();

        uint256 pending = totalRewardsOwing(_user).sub(stakers[_user].rewardDebt);
        if(pending > 0) {
            require(tokensClaimable == true,"Tokens cannnot be claimed yet");
            safeRewardsTransfer(msg.sender, pending);
        }
    }

    
    function emergencyUnstake()
        external 
    {
        Staker storage staker = stakers[msg.sender];
        uint256 amount = staker.balance;
        staker.balance = 0;
        staker.rewardDebt = 0;
        uint256 tokenBal = IERC20(lpToken).balanceOf(address(this));

        if(amount > tokenBal){
            IERC20(lpToken).safeTransfer(address(msg.sender), tokenBal);
        }else {
            IERC20(lpToken).safeTransfer(address(msg.sender),amount);
        }
        
    }


    function totalRewardsOwing(address _user)
        public
        
        returns(uint256)
    {   
        uint256 rewards =  stakers[_user].balance.mul(accRewardsPerToken).div(1e18);
        return rewards;
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

    // Returns the number of blocks remaining with the current rewards balance
    function blocksRemaining() public view returns (uint256){
        uint256 rewardsBal = rewardsToken.balanceOf(address(this));
        uint256 rewardsPerBlock = rewardsContract.LPRewardsPerBlock();
        if (rewardsPerBlock > 0) {
            return rewardsBal / rewardsPerBlock;
        } else {
            return 0;
        }
    } 

} 