import numpy as np
import dipy.segment.metric as dipymetric
from dipy.segment.featurespeed import extract

from nose.tools import assert_true, assert_false, assert_equal
from numpy.testing import (assert_array_equal, assert_array_almost_equal,
                           assert_raises, run_module_suite)


dtype = "float32"
s1 = np.array([np.arange(10, dtype=dtype)]*3).T  # 10x3
s2 = np.arange(3*10, dtype=dtype).reshape((-1, 3))[::-1]  # 10x3
s3 = np.random.rand(5, 4).astype(dtype)  # 5x4
s4 = np.random.rand(5, 3).astype(dtype)  # 5x3


def test_identity_feature():
    # Test subclassing Feature
    class Identity(dipymetric.Feature):
        def __init__(self):
            dipymetric.Feature.__init__(self, is_order_invariant=False)

        def infer_shape(self, streamline):
            return streamline.shape

        def extract(self, streamline):
            return streamline

    for feature in [dipymetric.IdentityFeature(), Identity()]:
        for s in [s1, s2, s3, s4]:
            # Test method infer_shape
            assert_equal(feature.infer_shape(s), s.shape)

            # Test method extract
            features = feature.extract(s)
            assert_equal(features.shape, s.shape)
            assert_array_equal(features, s)

        # This feature type is not order invariant
        assert_false(feature.is_order_invariant)
        for s in [s1, s2, s3, s4]:
            features = feature.extract(s)
            features_flip = feature.extract(s[::-1])
            assert_array_equal(features_flip, s[::-1])
            assert_true(np.any(np.not_equal(features, features_flip)))


def test_feature_center_of_mass():
    # Test subclassing Feature
    class CenterOfMass(dipymetric.Feature):
        def __init__(self):
            dipymetric.Feature.__init__(self, is_order_invariant=True)

        def infer_shape(self, streamline):
            return (1, streamline.shape[1])

        def extract(self, streamline):
            return np.mean(streamline, axis=0)[None, :]

    for feature in [dipymetric.CenterOfMassFeature(), CenterOfMass()]:
        for s in [s1, s2, s3, s4]:
            # Test method infer_shape
            assert_equal(feature.infer_shape(s), (1, s.shape[1]))

            # Test method extract
            features = feature.extract(s)
            assert_equal(features.shape, (1, s.shape[1]))
            assert_array_almost_equal(features, np.mean(s, axis=0)[None, :])

        # This feature type is order invariant
        assert_true(feature.is_order_invariant)
        for s in [s1, s2, s3, s4]:
            features = feature.extract(s)
            features_flip = feature.extract(s[::-1])
            assert_array_almost_equal(features, features_flip)


def test_feature_extract():
    # Test that features are automatically cast into float32 when coming from Python space
    class CenterOfMass64bit(dipymetric.Feature):
        def infer_shape(self, streamline):
            return streamline.shape[1]

        def extract(self, streamline):
            return np.mean(streamline.astype(np.float64), axis=0)

    nb_streamlines = 100
    feature_shape = (1, 3)  # One N-dimensional point
    feature = CenterOfMass64bit()

    streamlines = [np.arange(np.random.randint(20, 30) * 3).reshape((-1, 3)).astype(np.float32) for i in range(nb_streamlines)]
    features = extract(feature, streamlines)

    assert_equal(len(features), len(streamlines))
    assert_equal(features.shape[1:], feature_shape)

    # Test that scalar features
    class ArcLengthFeature(dipymetric.Feature):
        def infer_shape(self, streamline):
            return 1

        def extract(self, streamline):
            return np.sum(np.sqrt(np.sum((streamline[1:] - streamline[:-1]) ** 2)))

    nb_streamlines = 100
    feature_shape = (1, 1)  # One scalar represented as a 2D array
    feature = ArcLengthFeature()

    streamlines = [np.arange(np.random.randint(20, 30) * 3).reshape((-1, 3)).astype(np.float32) for i in range(nb_streamlines)]
    features = extract(feature, streamlines)

    assert_equal(len(features), len(streamlines))
    assert_equal(features.shape[1:], feature_shape)


def test_subclassing_feature():
    class EmptyFeature(dipymetric.Feature):
        pass

    feature = EmptyFeature()
    assert_raises(NotImplementedError, feature.infer_shape, None)
    assert_raises(NotImplementedError, feature.extract, None)


def test_using_python_feature_with_cython_metric():
    class Identity(dipymetric.Feature):
        def infer_shape(self, streamline):
            return streamline.shape

        def extract(self, streamline):
            return streamline

    # Test using Python Feature with Cython Metric
    feature = Identity()
    metric = dipymetric.AveragePointwiseEuclideanMetric(feature)
    d1 = dipymetric.dist(metric, s1, s2)

    features1 = metric.feature.extract(s1)
    features2 = metric.feature.extract(s2)
    d2 = metric.dist(features1, features2)
    assert_equal(d1, d2)


if __name__ == '__main__':
    run_module_suite()
