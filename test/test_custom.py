from queue import Queue
from shutil import which

import pytest

import yescommander as yc


def test_custom_soldier():
    c = yc.CalculatorSoldier()
    q = Queue()
    c.order(["1+" "3"], q)
    assert c.answer == "4"


# @pytest.mark.skipif(which("googler") is None, reason="Cannot find googler.")
# def test_custom_async():
#     import asyncio
#
#     from yc_googler import GooglerAsyncCommander
#
#     q = Queue()
#     gg = GooglerAsyncCommander()
#     asyncio.run(gg.order(["hello"], q))
#     q.get()
