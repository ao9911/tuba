"""
log_test.py - Unit tests for the log module.
"""

import pytest
from tuba.log import log


# Initialize logger before tests
def setup_module(module):
    cfg = log.Config(
        # log_path="/Users/chenjin/data/logs/",
        app_name="test",
        debug=False,
    )
    log.init(cfg)


def test_debug():
    log.debug("hello debug")
    log.debugf("hello number=%d", 100)


def test_info():
    log.info("hello")
    log.infof("hello number=%d", 100)


def test_warn():
    log.warn("hello")
    log.warnf("hello number=%d", 100)


def test_error():
    log.error("hello")
    log.errorf("hello number=%d", 100)


def test_fatal():
    # Skip actual fatal test as it exits the process
    # log.fatal("hello")
    # log.fatalf("hello number=%d", 100)
    pass


def test_ctx_info():
    token = log.with_trace_id("abc-123")
    log.ctx_info("abc-123", "hello world")
    log.reset_trace_id(token)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
