

from numpy import array
import unittest
import os
import sys

test_dir = os.path.dirname(os.path.abspath(__file__))
corpustools_path = os.path.split(os.path.split(os.path.split(test_dir)[0])[0])[0]
sys.path.insert(0,corpustools_path)
from corpustools.acousticsim.distance_functions import (dtw_distance,
                                    generate_distance_matrix,
                                    xcorr_distance)

class DTWTest(unittest.TestCase):
    def setUp(self):
        self.source = array([[2,3,4],
                            [5,6,7],
                            [2,7,6],
                            [1,5,6]])
        self.target = array([[5,6,7],
                            [2,3,4],
                            [6,8,3],
                            [2,7,9],
                            [1,5,8],
                            [7,4,9]])

    def test_dtw_unnorm(self):
        distmat = generate_distance_matrix(self.source, self.target)
        dist = dtw_distance(self.source,self.target,norm=False)

        r_dtw_output = 31.14363
        self.assertAlmostEqual(r_dtw_output, dist,places=5)

    def test_dtw_norm(self):
        distmat = generate_distance_matrix(self.source, self.target)
        dist = dtw_distance(self.source,self.target,norm=True)

        r_dtw_output = 3.114363
        self.assertAlmostEqual(r_dtw_output,dist,places=5)


if __name__ == '__main__':
    unittest.main()
