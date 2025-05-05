# pragma version 0.4.0

event TestEvent:
    value: uint256
    error: bool
    error_code: uint256

@external
def test_event():
    log TestEvent(value=1, error=True, error_code=2)
    log TestEvent(value=1, error=False) # @dev instanciation error
    log TestEvent(value=1, error=True, error_code=3)