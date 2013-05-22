__author__ = "David Rusk <drusk@uvic.ca>"

import unittest

from hamcrest import assert_that, equal_to

from mopgui.astrometry import wcs


class WCSTest(unittest.TestCase):
    def test_get_order_1(self):
        pv = [range(3), range(3)]
        assert_that(wcs.get_order(pv), equal_to(1))

    def test_get_order_2(self):
        pv = [range(6), range(6)]
        assert_that(wcs.get_order(pv), equal_to(2))

    def test_get_order_3(self):
        pv = [range(10), range(10)]
        assert_that(wcs.get_order(pv), equal_to(3))


if __name__ == '__main__':
    unittest.main()
