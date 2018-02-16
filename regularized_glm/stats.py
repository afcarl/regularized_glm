def _weighted_design_matrix_svd(design_matrix, sqrt_penalty_matrix, weights):
    _, R = np.linalg.qr(np.sqrt(weights[:, np.newaxis]) * design_matrix)
    U, singular_values, Vt = np.linalg.svd(
        np.concatenate((R, sqrt_penalty_matrix)), full_matrices=False)
    n_covariates = design_matrix.shape[1]

    # Keep the linearly independent columns using svd
    svd_error = singular_values.max() * np.max(design_matrix.shape) * np.finfo(singular_values.dtype).eps
    U = U[:n_covariates, singular_values > svd_error];

    return U, singular_values, Vt


def get_effective_degrees_of_freedom(U):
    return np.sum(U.ravel() * U.ravel()) # np.trace(U @ U.T), trace of the influence matrix


def get_coefficient_covariance(U, singular_values, Vt):
PKt = Vt @ np.diag(1 / singular_values) @ U.T
return PKt @ PKt.T # Frequentist Covariance Sandwich Estimator