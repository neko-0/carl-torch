import logging
import numpy as np
import json
import os

from sklearn.utils import column_or_1d
from sklearn.preprocessing import LabelEncoder

from .utils.tools import load_and_check
from .distributions import Histogram
from .utils.tools import create_missing_folders, load_and_check
from .ratio import RatioEstimator

logger = logging.getLogger(__name__)

class CalibratedClassifier():
    """Probability calibration.
    """

    def __init__(self, model, method="histogram", bins=100,
                 interpolation=None, variable_width=False):
        """Constructor.
        Parameters
        ----------
        """
        self.method = method
        self.bins = bins
        self.interpolation = interpolation
        self.variable_width = variable_width
        self.model = model
    def fit(self, X, y):
        """Fit the calibrated model.
        Parameters
        ----------
        * `X` [array-like, shape=(n_samples, n_features)]:
            Training data.
        * `y` [array-like, shape=(n_samples,)]:
            Target values.
        Returns
        -------
        * `self` [object]:
            `self`.
        """
        # Check inputs
        X = load_and_check(X)
        y = load_and_check(y)
        y = column_or_1d(y)
        label_encoder = LabelEncoder()
        y = label_encoder.fit_transform(y).astype(np.float)

        if len(label_encoder.classes_) != 2:
            raise ValueError
        self.classes_ = label_encoder.classes_

        # Calibrator
        cal = HistogramCalibrator(bins=self.bins, interpolation=self.interpolation,variable_width=self.variable_width)
        _, T = self.model.evaluate(X)

        cal.fit(T, y)
        self.calibrator = cal
        return self

    def predict(self, X):
        """Predict the targets for `X`.
        Can be different from the predictions of the uncalibrated classifier.
        Parameters
        ----------
        * `X` [array-like, shape=(n_samples, n_features)]:
            The samples.
        Returns
        -------
        * `y` [array, shape=(n_samples,)]:
            The predicted class.
        """
        X = load_and_check(X)
        _, s_hat = self.model.evaluate(X)
        p = self.predict_proba(X, s_hat)
        p[p == np.inf] = 1
        p[p == 0] = 1       
        return p[:, 0], p[:, 1], np.divide(p[:, 0], p[:, 1])


    def predict_proba(self, X, s_hat):
        """Predict the posterior probabilities of classification for `X`.
        Parameters
        ----------
        * `X` [array-like, shape=(n_samples, n_features)]:
            The samples.
        Returns
        -------
        * `probas` [array, shape=(n_samples, n_classes)]:
            The predicted probabilities.
        """
        p = np.zeros((len(X), 2))
        p[:, 1] += self.calibrator.predict(s_hat)
        p[:, 0] = 1. - p[:, 1]
        return p


class HistogramCalibrator():
    """Probability calibration through density estimation with histograms."""

    def __init__(self, bins="auto", range=None, eps=0.1,
                 interpolation=None, variable_width=False):
        """Constructor.
        Parameters
        ----------
        * `bins` [string or integer]:
            The number of bins, or `"auto"` to automatically determine the
            number of bins depending on the number of samples.
        * `range` [(lower, upper), optional]:
            The lower and upper bounds. If `None`, bounds are automatically
            inferred from the data.
        * `eps` [float]:
            The margin to the lower and upper bounds.
        * `interpolation` [string, optional]:
            Specifies the kind of interpolation between bins as a string
            (`"linear"`, `"nearest"`, `"zero"`, `"slinear"`, `"quadratic"`,
            `"cubic"`).
        * `variable_width` [boolean, optional]
            If True use equal probability variable length bins.
        """
        self.bins = bins
        self.range = range
        self.eps = eps
        self.interpolation = interpolation
        self.variable_width = variable_width

    def fit(self, T, y):
        """Fit using `T`, `y` as training data.
        Parameters
        ----------
        * `T` [array-like, shape=(n_samples,)]:
            Training data.
        * `y` [array-like, shape=(n_samples,)]:
            Training target.
        Returns
        -------
        * `self` [object]:
            `self`.
        """
        # Check input
        T = column_or_1d(T)
        t0 = T[y == 0]
        t1 = T[y == 1]
        bins = self.bins
        if self.bins == "auto":
            bins = 10 + int(len(t0) ** (1. / 3.))
        range = self.range
        if self.range is None:
            t_min = max(0, min(np.min(t0), np.min(t1)) - self.eps)
            t_max = min(1, max(np.max(t0), np.max(t1)) + self.eps)
            range = [(t_min, t_max)]
        # Fit
        self.calibrator0 = Histogram(bins=bins, range=range,
                                     interpolation=self.interpolation,
                                     variable_width=self.variable_width)
        self.calibrator1 = Histogram(bins=bins, range=range,
                                     interpolation=self.interpolation,
                                     variable_width=self.variable_width)
        self.calibrator0.fit(t0.reshape(-1, 1))
        self.calibrator1.fit(t1.reshape(-1, 1))
        return self

    def predict(self, T):
        """Calibrate data.
        Parameters
        ----------
        * `T` [array-like, shape=(n_samples,)]:
            Data to calibrate.
        Returns
        -------
        * `Tt` [array, shape=(n_samples,)]:
            Calibrated data.
        """
        T = column_or_1d(T).reshape(-1, 1)
        num = self.calibrator1.pdf(T)
        den = self.calibrator0.pdf(T) + self.calibrator1.pdf(T)
        p = num / den
        p[den == 0] = 0.5
        return p
        
