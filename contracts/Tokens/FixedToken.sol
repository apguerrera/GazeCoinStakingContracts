pragma solidity 0.6.12;

import "./ERC20.sol";
import "../../../interfaces/IGazeToken.sol";
contract FixedToken is ERC20, IGazeToken{

    
    /// @dev First set the token variables. This can only be done once
    function initToken(string memory _name, string memory _symbol, uint256 _initialSupply) public override {
        _initERC20(_name, _symbol);
        _mint(msg.sender, _initialSupply);
    }


}
