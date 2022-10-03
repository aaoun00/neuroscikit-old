"""
This module contains functions for extracting waveform features for each unit.

- Functions for extracting a long feature vector for each unit.
- Functions for summarizing aggregated unit features.
"""


# Utility functions for comparing distributions

#TODO test
def jensen_shannon_distance(P:np.array, Q:np.array):
    """Compute the Jensen-Shannon distance between two probability distributions.

    Input
    -----
    P, Q : 2D arrays (sample_size, dimensions)
        Probability distributions of equal length that sum to 1
    """
    P_sample_size, P_dimensions = P.shape
    Q_sample_size, Q_dimensions = Q.shape
    assert P_dimensions == Q_dimensions, f"Dimensionality of P ({P_dimensions}) and Q ({Q_dimensions}) must be equal"
    dimensions = P_dimensions
    M = 0.5 * (P + Q)

    if dimensions == 1:
        _kldiv = lambda A, B: np.sum([v for v in A * np.log(A/B) if not np.isnan(v)])
    if dimensions > 1:
        _kldiv = lambda A, B: multivariate_kullback_leibler_divergence(A, B)
    else:
        raise ValueError(f"Dimensionality of P ({P_dimensions}) and Q ({Q_dimensions}) must be greater than 0")

    result = np.sqrt(0.5 * (_kldiv(P, M) +_kldiv(Q, M)))
    return np.sqrt(result)

#TODO test
def kullback_leibler_divergence(P, Q):

    return np.sum(list(filter(lambda x: not np.isnan(x), P * np.log(P/Q))))

#TODO test
def multivariate_kullback_leibler_divergence(x, y):
    """Compute the Kullback-Leibler divergence between two multivariate samples.
    Parameters
    ----------
    x : 2D array (sample_size, dimensionality)
        Samples from distribution P, which typically represents the true
        distribution.
    y : 2D array (sample_size, dimensionality)
        Samples from distribution Q, which typically represents the approximate
        distribution.
    Returns
    -------
    out : float
        The estimated Kullback-Leibler divergence D(P||Q).
    References
    ----------
    Pérez-Cruz, F. Kullback-Leibler divergence estimation of
    continuous distributions IEEE International Symposium on Information
    Theory, 2008.
    Adapted from https://gist.github.com/atabakd/ed0f7581f8510c8587bc2f41a094b518
    """
    from scipy.spatial import cKDTree as KDTree

    # Check the dimensions are consistent
    x = np.atleast_2d(x)
    y = np.atleast_2d(y)

    x_sample_size, x_dimensions = x.shape
    y_sample_size, y_dimensions = y.shape

    assert(x_dimensions == y_dimensions), f"Both samples must have the same number of dimensions. x has {x_dimensions} dimensions, while y has {y_dimensions} dimensions."


    # Build a KD tree representation of the samples and find the nearest neighbour
    # of each point in x.
    xtree = KDTree(x)
    ytree = KDTree(y)

    # Get the first two nearest neighbours for x, since the closest one is the
    # sample itself.
    r = xtree.query(x, k=2, eps=.01, p=2)[0][:,1]
    s = ytree.query(x, k=1, eps=.01, p=2)[0]

    # There is a mistake in the paper. In Eq. 14, the right side misses a negative sign
    # on the first term of the right hand side.
    return -np.log(r/s).sum() * d / n + np.log(m / (n - 1.))