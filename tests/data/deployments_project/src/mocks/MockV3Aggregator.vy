# SPDX-License-Identifier: MIT
# pragma version 0.4.0

DECIMALS: immutable(uint8)
latestAnswer: public(int256)
latestTimestamp: public(uint256)
latestRound: public(uint256)

getAnswer: public(HashMap[uint256, int256])
getTimestamp: public(HashMap[uint256, uint256])
getStartedAt: public(HashMap[uint256, uint256])

supply: uint256
decimals: uint256

version: public(constant(uint256)) = 2

@internal
def updateAnswer(_answer: int256):
    self.latestAnswer = _answer
    self.latestTimestamp = block.timestamp
    self.latestRound = self.latestRound + 1
    self.getAnswer[self.latestRound] = _answer 
    self.getTimestamp[self.latestRound] = block.timestamp
    self.getStartedAt[self.latestRound] = block.timestamp

@deploy
def __init__(_decimals: uint8, _initialAnswer: int256):
    DECIMALS = _decimals
    self.updateAnswer(_initialAnswer)

@external
def updateRoundData(_roundId: uint256, _answer: int256, _timestamp: uint256, _startedAt: uint256):
    self.latestRound = _roundId
    self.latestAnswer = _answer
    self.latestTimestamp = _timestamp
    self.getAnswer[self.latestRound] = _answer
    self.getTimestamp[self.latestRound] = _timestamp
    self.getStartedAt[self.latestRound] = _startedAt

@external
@view 
def getRoundData(_roundId: uint256) -> (uint256, int256, uint256, uint256, uint256): 
    return (_roundId, self.getAnswer[_roundId], self.getStartedAt[_roundId], self.getTimestamp[_roundId], _roundId)


@external
@view 
def latestRoundData() -> (uint256, int256, uint256, uint256, uint256): 
    return (self.latestRound, self.getAnswer[self.latestRound], self.getStartedAt[self.latestRound], self.getTimestamp[self.latestRound], self.latestRound)