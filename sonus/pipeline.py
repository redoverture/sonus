"""
Code to process data in a Pipeline.
"""

import sys
import pandas as pd
import numpy as np
import sklearn
import scipy
import statistics as stat
import math
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import VarianceThreshold


def generate_pipeline(model):
    return Pipeline(
            [("Scaler", StandardScaler()), ("Zero Var Remover", VarianceThreshold(threshold=0.8)), ("Model", model)])


def statistics(data: np.ndarray):
    """
    based on the data given, creates features such as min, max, mean, std, rms, percentiles; 0, 25, 50, and 75
    :param data: np.ndarray the data used to create statistics/features from
    :return: np.ndarray new features as columns
    """
    NUM_STATS = 9

    result = np.zeros(shape=(len(data), NUM_STATS))

    result[:, 0] = data.max(axis=1)
    result[:, 1] = data.min(axis=1)
    result[:, 2] = data.mean(axis=1)
    result[:, 3] = np.std(data, axis=1)
    result[:, 4] = np.sqrt(np.sum((data ** 2) / data.shape[1], axis=1))
    result[:, 5] = np.percentile(data, 0, axis=1)
    result[:, 6] = np.percentile(data, 25, axis=1)
    result[:, 7] = np.percentile(data, 50, axis=1)
    result[:, 8] = np.percentile(data, 75, axis=1)

    return result


def arg_statistics(data: np.ndarray):
    """
    Perform similar analysis to pipeline.statistics, but return the indexes instead of the values.
    :param data: np.ndarray the data used to create statistics/features from
    :return: np.ndarray new features as columns
    """

    NUM_STATS = 7

    result = np.zeros(shape=(len(data), NUM_STATS))

    result[:, 0] = data.argmax(axis=1)
    result[:, 1] = data.argmin(axis=1)

    # Unfortunately vectorized arg functions end here...
    for idx, row in enumerate(data):
        sys.stdout.write(f"\r[-] Arg-Stat: {idx} of {len(data)} ({idx / len(data) * 100: .2f}%)")
        sys.stdout.flush()
        result[idx, 2] = np.argsort(row)[len(row) // 2]  # nlogn each row, n * nlogn total
        result[idx, 3] = np.argwhere(row == (np.percentile(row, 0, interpolation='nearest')))[0]
        result[idx, 4] = np.argwhere(row == (np.percentile(row, 25, interpolation='nearest')))[0]
        result[idx, 5] = np.argwhere(row == (np.percentile(row, 50, interpolation='nearest')))[0]
        result[idx, 6] = np.argwhere(row == (np.percentile(row, 75, interpolation='nearest')))[0]
    sys.stdout.write(f"\r[-] Arg-Stat: Completed {len(data)} (100%)\n")
    sys.stdout.flush()

    return result


def fft(data: np.ndarray, low_pass=20, high_pass=20000, return_x=False):
    """
    Adds a frequency space feature to the data. The data should be a windowed audio array.
    The output of this algorithm is appended columns at the end.
    https://makersportal.com/blog/2018/9/13/audio-processing-in-python-part-i-sampling-and-the-fast-fourier-transform
    https://www.youtube.com/watch?v=17cOaqrwXlo
    https://www.youtube.com/watch?v=aQKX3mrDFoY  << Especially helpful
    https://github.com/markjay4k/Audio-Spectrum-Analyzer-in-Python
    :param return_x: Return the FFT x-axis.
    :param high_pass: Where to stop reporting, at the higher end of the FFT
    :param low_pass: Where to start reporting the low end of the FFT
    :param data: np.ndarray Windowed audio data for training
    :return: np.ndarray with appended columns, extra length of high_pass-low_pass. (or tuple x_axis, np.ndarray)
    """

    assert high_pass > low_pass, f"Invalid FFT window {low_pass} to {high_pass}"

    n_samples = data.shape[1]
    fft_ys = []

    fft_x = scipy.fft.fftfreq(n_samples, (1.0 / 16000))  # 16000 is the sample rate
    fft_x = fft_x[0:(n_samples // 2)]  # Take the first half of the x-axis too
    pass_mask = [True if low_pass <= x <= high_pass else False for x in fft_x]
    fft_x = fft_x[pass_mask]

    for i, row in enumerate(data):
        sys.stdout.write(f"\r[-] FFT: {i} of {len(data)} ({i / len(data) * 100: .2f}%)")
        sys.stdout.flush()
        n_samples = len(row)
        fft_y = scipy.fft(row)
        fft_y = np.abs(fft_y[0:(n_samples // 2)])  # Take real components of first half
        # fft_y = np.multiply(fft_y, 2) / (32767 * (n_samples // 2))  # Rescale, 16-bit PCM
        fft_y = np.divide(np.multiply(fft_y, 2), n_samples)
        fft_y = fft_y[pass_mask]  # Mask out unwanted values
        fft_ys.append(fft_y)
    sys.stdout.write(f"\r[-] FFT: Completed {len(data)} (100%)\n")
    sys.stdout.flush()

    fft_ys = np.array(fft_ys)
    # result = np.concatenate((data, fft_ys), axis=1)

    if not return_x:
        return fft_ys
    else:
        return fft_x, fft_ys


def column_join(*data):
    """
    Takes any number of np.ndarray to concatenate on the column dimension.
    This can combine data from multiple sources to be used with an ML model.
    :param data: np.ndarrays with equal numbers of rows.
    :return: One single np.ndarray, concatenated on columns.
    """
    assert len(data) > 1, f"Need at least 2 arrays to join. Got {len(data)}."
    assert type(data[0]) is np.ndarray
    expected_rows = data[0].shape[0]

    result = data[0]

    for item in data[1:]:
        assert type(item) is np.ndarray
        assert item.shape[0] == expected_rows, f"Rows must be equal length. Expected {expected_rows}, " \
                                               f"got {item.shape[0]}."

        result = np.concatenate((result, item), axis=1)

    return result


def diff(data: np.ndarray):
    """
    calculates the derivative of the data
    :param data: the data to take the derivative of
    :return: the derivative
    """
    return np.diff(data)
