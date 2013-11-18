# -*- coding: utf-8 -*-

__all__ = ['RPIO', 'delay_us', 'delay_ms', 'bv']


import time


try:
    import RPIO
except ImportError:
    try:
        import RPi.GPIO as RPIO
    except ImportError:
        raise ImportError ('You must have RPIO or RPi package')


def delay_us (useconds):
    time.sleep (useconds / float (1000000))


def delay_ms (mseconds):
    time.sleep (mseconds / float (1000))


def bv (*bits):
    result = 0
    for bit in bits:
        result |= 1 << bit
    return result

