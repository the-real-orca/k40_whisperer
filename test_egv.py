
""" Perform unit tests on the egv.py file
"""


import unittest

import egv

class TestegvClass(unittest.TestCase):
    def setUp(self):
        self.data = []
        self.object = egv.egv(target=lambda s:self.data.append(s))

    def tearDown(self):
        self.object = None

    def test_move(self):

        tests = [
            { 'dir':        0, 'dist':  0, 'laser': False, 'expect': '' },
            { 'dir': ord('B'), 'dist':  1, 'laser': False, 'expect': 'Ba' },
            { 'dir': ord('T'), 'dist':  1, 'laser': False, 'expect': 'Ta' },
            { 'dir': ord('L'), 'dist':  1, 'laser': False, 'expect': 'La' },
            { 'dir': ord('R'), 'dist':  1, 'laser': False, 'expect': 'Ra' },
            { 'dir': ord('M'), 'dist':  1, 'laser': False, 'expect': 'Ma' },
            { 'dir':  0, 'dist':  0, 'laser': True,  'expect': 'D' },
            { 'dir':  0, 'dist':  0, 'laser': False, 'expect': 'U' },
        ]

        # TODO
        # - need to write code to exercise the angle_dirs, but I dont quite
        #   understand what they are trying to achieve yet

        for test in tests:
            self.data = []
            self.object.move( test['dir'], test['dist'], test['laser'] )
            self.object.flush()
            got = "".join(map(chr, self.data))
            self.assertEqual( got, test['expect'] )

    def test_flush(self):
        tests = [
            { 'laser': False, 'expect': '' },
            { 'laser': True,  'expect': 'D' },
            { 'laser': False, 'expect': 'U' },
        ]

        for test in tests:
            self.data = []
            self.object.flush(laser_on=test['laser'])
            got = "".join(map(chr, self.data))
            self.assertEqual( got, test['expect'] )

#
# This file has a syntax error in OneWireCRC - the return tries to return
# an undefined variable.
#
# Thus - assume that function is unused for the moment
#
#    def test_OneWireCRC(self):
#        self.assertEqual(
#            self.object.OneWireCRC([fixme]),
#            fixme
#        )

    def test_make_distance(self):
        with self.assertRaises(StandardError):
            self.object.make_distance(1.1)

        # What a strange number coding.  I guess they had never heard of
        # Huffman, or ASN.1 BER
        tests = [
            { 'mils':    0, 'expect': '' },
            { 'mils':    1, 'expect': 'a' },
            { 'mils':   25, 'expect': 'y' },
            { 'mils':   26, 'expect': '|a' },
            { 'mils':   51, 'expect': '|z' },
            { 'mils':   52, 'expect': '052' },
            { 'mils':  254, 'expect': '254' },
            { 'mils':  255, 'expect': 'z' },
            { 'mils':  256, 'expect': 'za' },
            { 'mils':  511, 'expect': 'zza' },
            { 'mils':  766, 'expect': 'zzza' },
            { 'mils': 1021, 'expect': 'zzzza' },
        ]

        for test in tests:
            got = "".join(map(chr, self.object.make_distance( test['mils'] )))
            self.assertEqual( got, test['expect'] )

    def test_make_dir_dist(self):

        tests = [
            { 'x':  0, 'y':  0, 'expect': '' },
            { 'x':  0, 'y':  1, 'expect': 'La' },       # Left
            { 'x':  0, 'y': -1, 'expect': 'Ra' },       # Right
            { 'x':  1, 'y':  0, 'expect': 'Ba' },       # Bottom
            { 'x': -1, 'y':  0, 'expect': 'Ta' },       # Top
        ]

        # make_dir_dist() is an up/down then left/right mover
        # TODO - test with laser_on=True (perhaps in test_move)

        for test in tests:
            self.data = []
            self.object.make_dir_dist( test['x'], test['y'] )
            self.object.flush()
            got = "".join(map(chr, self.data))
            self.assertEqual( got, test['expect'] )

    def test_make_cut_line(self):
        with self.assertRaises(StandardError):
            self.object.make_cut_line(1.1,1.1)

        tests = [
            { 'x':  0, 'y':  0, 'expect': 'D' },
            { 'x':  0, 'y':  1, 'expect': 'La' },
            { 'x':  0, 'y': -1, 'expect': 'Ra' },
            { 'x':  1, 'y':  0, 'expect': 'Ba' },
            { 'x': -1, 'y':  0, 'expect': 'Ta' },
            { 'x': 10, 'y': 10, 'expect': 'BLMj' },
            { 'x':  1, 'y':  1, 'expect': 'Ma' },
            { 'x': -1, 'y': -1, 'expect': 'TRMa' },
            { 'x': 16, 'y':  9, 'expect': 'BLMaBaMaBaMaBaMbBaMaBaMaBaMaBaMa' },
            { 'x': -9, 'y': 16, 'expect':  'TMaLaMaLaMaLaMbLaMaLaMaLaMaLaMa' },
            { 'x': 100, 'y': 7, 'expect': 'BgMaBmMaBmMaBnMaBmMaBmMaBmMaBg' },
        ]

        for test in tests:
            self.data = []
            self.object.make_cut_line( test['x'], test['y'] )
            self.object.flush()
            got = "".join(map(chr, self.data))
            self.assertEqual( got, test['expect'] )

    def test_make_speed(self):
        with self.assertRaises(TypeError):
            self.object.make_speed()
        with self.assertRaises(StandardError):
            self.object.make_speed(board_name='larry')
        with self.assertRaises(ZeroDivisionError):
            self.object.make_speed(Feed=0)
        with self.assertRaises(UnboundLocalError):
            self.object.make_speed(Feed=0.7, board_name='LASER-B1')

        tests = [
            { 'f':   1, 'b': 'LASER-M2', 's': 0, 'e': 'CV1551931000000000C' },
            { 'f':   6, 'b': 'LASER-M2', 's': 0, 'e': 'CV2390681000000000C' },
            { 'f':   7, 'b': 'LASER-M2', 's': 0, 'e': 'CV0640541000000000' },
            { 'f': 100, 'b': 'LASER-M2', 's': 0, 'e': 'CV2232481000000000' },
            { 'f': 100, 'b': 'LASER-M2', 's': 1, 'e':  'V2232481G001' },
            { 'f': 100, 'b': 'LASER-M2', 's': 9, 'e':  'V2232481G009' },
            { 'f': 0.8, 'b': 'LASER-B1', 's': 0, 'e': 'CV0042281000000000' },
            { 'f':   1, 'b': 'LASER-B1', 's': 0, 'e': 'CV0541281000000000' },
            { 'f':  10, 'b': 'LASER-B1', 's': 0, 'e': 'CV2330241000000000' },
            { 'f': 100, 'b': 'LASER-B1', 's': 0, 'e': 'CV2502431000000000' },
            { 'f': 100, 'b': 'LASER-B1', 's': 1, 'e':  'V2502431G001' },
            { 'f': 100, 'b': 'LASER-B1', 's': 9, 'e':  'V2502431G009' },
        ]

        for test in tests:
            got = "".join(map(chr,
                self.object.make_speed(
                    Feed=test['f'],
                    board_name=test['b'],
                    Raster_step=test['s']
                )
            ))
            self.assertEqual( got, test['e'] )


    def test_make_move_data(self):

        tests = [
            { 'x': 0, 'y': 0, 'expect': '' },
            { 'x': 1, 'y': 1, 'expect': 'ILaBaS1P' },
            { 'x': 1000, 'y': 1000, 'expect': 'ILzzz235Bzzz235S1P' },
        ]

        # make_move_data() is essentially a wrapper around make_distance():
        # "I" "L{}" "B{}" "S1P", with the two {} filled in by make_distance

        for test in tests:
            self.data = []
            self.object.make_move_data( test['x'], test['y'] )
            got = "".join(map(chr, self.data))
            self.assertEqual( got, test['expect'] )

    def test_ecoord_adj(self):

        tests = [
            { 'adj': [0,0,0],  'scale': 0, 'flip': 0, 'expect': (0,0,0) },
            { 'adj': [0,0,10], 'scale': 1, 'flip': 0, 'expect': (0,0,10) },
            { 'adj': [0,0,10], 'scale': 2, 'flip': 0, 'expect': (0,0,10) },
            { 'adj': [0,10,0], 'scale': 1, 'flip': 0, 'expect': (0,10,0) },
            { 'adj': [0,10,0], 'scale': 2, 'flip': 0, 'expect': (0,20,0) },
            { 'adj': [10,0,0], 'scale': 1, 'flip': 0, 'expect': (10,0,0) },
            { 'adj': [10,0,0], 'scale': 2, 'flip': 0, 'expect': (20,0,0) },
            { 'adj': [10,0,0], 'scale': 2, 'flip': 4, 'expect': (-12,0,0) },
        ]

        for test in tests:
            got = self.object.ecoord_adj(
                ecoords_adj_in=test['adj'],
                scale=test['scale'],
                FlipXoffset=test['flip']
            )
            self.assertEqual( got, test['expect'] )

    def test_make_egv_data(self):
        # yet another unreachable section of code
        with self.assertRaises(TypeError):
            self.object.make_egv_data([[0,0,0],[0,0,0]], Feed=None)

        tests = [
            {
                'param': {
                    'ecoords_in': [[0,0,0],[0,0,0]], 'Feed': 1,
                },
                'expect': 'ICV1551931000000000CNRBS1EFNSE',
            },
            {
                'param': {
                    'ecoords_in': [[0,0,0],[0,0,0]], 'Feed': 1,
                    'startX': 0.01, 'startY': 0.02,
                },
                'expect': 'ICV1551931000000000CRtTjNRBS1ETcLcTNLqBmSEFNSE',
            },
            {
                'param': {
                    'ecoords_in': [[0,0,0],[0,0,0]], 'Feed': 1,
                    'units': 'mm',
                    'startX': 0.2, 'startY': 0.4,
                },
                'expect': 'ICV1551931000000000CRpThNRBS1ETcLcTNLmBkSEFNSE',
            },
            {
                'param': {
                    'ecoords_in': [[0,0,0],[0.1,0,1],[0.1,0.1,0],[0,0.1,1]],
                    'Feed': 1,
                },
                'expect': 'ICV1551931000000000CNRBS1ETcLcTNRcB103SETcLcTNL097BcSETcLcBNRcT097SETcLcTNR103BcSEFNSE',
            },
            {
                'param': {
                    'ecoords_in': [[0,0,1],[0.1,0,1],[0.1,0.1,0],[0,0.1,0]],
                    'Feed': 1,
                },
                'expect': 'ICV1551931000000000CNRBS1EDB100UTcLcTNL097BcSEDT100UTcLcTNR103BcSEFNSE',
            },
            {
                'param': {
                    'ecoords_in': [[0,0,1],[0.004,0,1],[0.004,0.004,0],[0,0.004,0]],
                    'Feed': 1,
                },
                'expect': 'ICV1551931000000000CNRBS1EDBdULdDTdURdFNSE',
            },
        ]

        # TODO
        # - raster

        for test in tests:
            self.data = []
            self.object.make_egv_data(**test['param'])
            got = "".join(map(chr, self.data))
            self.assertEqual( got, test['expect'] )
