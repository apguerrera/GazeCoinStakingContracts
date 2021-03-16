// SPDX-License-Identifier: GPLv2

pragma solidity 0.6.12;

/// @dev an interface to interact with the Genesis MONA NFT that will 
interface IGazeRewards {
    function updateRewards() external returns (bool);
    function LPRewards(uint256 _from, uint256 _to) external view returns (uint256);
}
