import numpy as np
from statsmodels.api import families


def _weighted_design_matrix_svd(design_matrix, sqrt_penalty_matrix, weights):
    '''

    Parameters
    ----------
    design_matrix : ndarray, shape (n_observations, n_covariates)
    sqrt_penalty_matrix : ndarray, shape (n_observations, n_observations)
    weights : ndarray, shape (n_observations,)

    Returns
    -------
    U : ndarray, shape (n_observations, n_independent)
    singular_values : ndarray, shape (n_independent, n_independent)
    Vt : ndarray, shape ()

    '''
    _, R = np.linalg.qr(np.sqrt(weights[:, np.newaxis]) * design_matrix)
    U, singular_values, Vt = np.linalg.svd(
        np.concatenate((R, sqrt_penalty_matrix)), full_matrices=False)
    n_covariates = design_matrix.shape[1]

    # Keep the linearly independent columns using svd
    svd_error = (singular_values.max() * np.max(design_matrix.shape)
                 * np.finfo(singular_values.dtype).eps)
    is_independent = singular_values > svd_error
    U = U[:n_covariates, is_independent]
    singular_values = singular_values[is_independent, is_independent]
    Vt = Vt[:, is_independent]

    return U, singular_values, Vt


def get_effective_degrees_of_freedom(U):
    '''Degrees of freedom that account for regularization.

    Parameters
    ----------
    U : ndarray, shape (n_observations, n_independent)

    Returns
    -------
    effective_degrees_of_freedom : int or float

    '''
    return np.sum(U * U)


def get_coefficient_covariance(U, singular_values, Vt, scale):
    '''Frequentist Covariance Sandwich Estimator.

    Parameters
    ----------
    U : ndarray, shape (n_observations, n_independent)
    singular_values : ndarray, shape (n_independent, n_independent)
    Vt : ndarray, shape ()
    scale : float

    Returns
    -------
    coefficient_covariance : ndarray, shape (n_independent, n_independent)

    '''
    PKt = Vt @ np.diag(1 / singular_values) @ U.T
    return PKt @ PKt.T * scale


def pearson_chi_square(response, predicted_response, prior_weights, variance,
                       degrees_of_freedom):
    '''Pearson’s chi-square statistic.

    Parameters
    ----------
    response : ndarray, shape (n_observations,)
    predicted_response : ndarray, shape (n_observations,)
    prior_weights : ndarray, shape (n_observations,)
    variance : function
    degrees_of_freedom : int or float

    Returns
    -------
    chi_square : float

    '''
    residual = response - predicted_response
    residual_degrees_of_freedom = response.shape[0] - degrees_of_freedom
    chi_square = prior_weights * residual ** 2 / variance(predicted_response)
    return np.sum(chi_square) / residual_degrees_of_freedom


def estimate_scale(family, response, predicted_response, prior_weights,
                   degrees_of_freedom):
    '''If the scale has to be estimated, the scale is estimated as Pearson's
    chi square.

    Parameters
    ----------
    family : statsmodels.api.families instance
    response : ndarray, shape (n_observations,)
    predicted_response : ndarray, shape (n_observations,)
    prior_weights : ndarray, shape (n_observations,)
    degrees_of_freedom : int or float

    Returns
    -------
    scale : float
    is_estimated_scale : bool

    '''
    if isinstance(family, (families.Binomial, families.Poisson)):
        scale = 1.0
        is_estimated_scale = False
    else:
        scale = pearson_chi_square(
            response, predicted_response, prior_weights, family.variance,
            degrees_of_freedom)
        is_estimated_scale = True
    return scale, is_estimated_scale


def estimate_aic(log_likelihood, degrees_of_freedom,
                 is_estimated_scale):
    '''Akaike information criterion.

    Parameters
    ----------
    log_likelihood : float
    degrees_of_freedom : float
    is_estimated_scale : bool

    Returns
    -------
    Akaike_information_criterion : float

    '''
    return (-2 * log_likelihood + 2 * (degrees_of_freedom + 1)
            + 2 * is_estimated_scale)
