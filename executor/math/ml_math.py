"""
Machine Learning Mathematics Module
===================================

Comprehensive mathematical foundations for machine learning including:
- Neural network mathematics (activation functions, loss functions, backpropagation)
- Kernel methods (RBF, polynomial, sigmoid, etc.)
- Optimization algorithms (SGD, Adam, RMSprop, etc.)
- Information theory (entropy, KL divergence, mutual information)
- Matrix calculus (gradients, Jacobians, Hessians)
- Dimensionality reduction (PCA, SVD)
- Regularization theory
"""

import math
from typing import List, Dict, Tuple, Callable, Optional, Union
from functools import lru_cache


class MLMath:
    """Machine Learning Mathematics - comprehensive ML mathematical foundations"""

    # ==========================================
    # ACTIVATION FUNCTIONS
    # ==========================================

    def sigmoid(self, x: float) -> float:
        """Logistic sigmoid activation: 1 / (1 + e^(-x))"""
        if x >= 0:
            return 1.0 / (1.0 + math.exp(-x))
        else:
            # Numerically stable for negative x
            exp_x = math.exp(x)
            return exp_x / (1.0 + exp_x)

    def sigmoid_derivative(self, x: float) -> float:
        """Derivative of sigmoid: sigmoid(x) * (1 - sigmoid(x))"""
        s = self.sigmoid(x)
        return s * (1 - s)

    def tanh(self, x: float) -> float:
        """Hyperbolic tangent activation"""
        return math.tanh(x)

    def tanh_derivative(self, x: float) -> float:
        """Derivative of tanh: 1 - tanh^2(x)"""
        t = math.tanh(x)
        return 1 - t * t

    def relu(self, x: float) -> float:
        """Rectified Linear Unit: max(0, x)"""
        return max(0.0, x)

    def relu_derivative(self, x: float) -> float:
        """Derivative of ReLU: 1 if x > 0 else 0"""
        return 1.0 if x > 0 else 0.0

    def leaky_relu(self, x: float, alpha: float = 0.01) -> float:
        """Leaky ReLU: x if x > 0 else alpha * x"""
        return x if x > 0 else alpha * x

    def leaky_relu_derivative(self, x: float, alpha: float = 0.01) -> float:
        """Derivative of Leaky ReLU"""
        return 1.0 if x > 0 else alpha

    def elu(self, x: float, alpha: float = 1.0) -> float:
        """Exponential Linear Unit: x if x > 0 else alpha * (e^x - 1)"""
        return x if x > 0 else alpha * (math.exp(x) - 1)

    def elu_derivative(self, x: float, alpha: float = 1.0) -> float:
        """Derivative of ELU"""
        return 1.0 if x > 0 else alpha * math.exp(x)

    def selu(self, x: float) -> float:
        """Scaled Exponential Linear Unit (self-normalizing)"""
        alpha = 1.6732632423543772848170429916717
        scale = 1.0507009873554804934193349852946
        return scale * (x if x > 0 else alpha * (math.exp(x) - 1))

    def gelu(self, x: float) -> float:
        """Gaussian Error Linear Unit (approximate)"""
        return 0.5 * x * (1 + math.tanh(math.sqrt(2 / math.pi) * (x + 0.044715 * x**3)))

    def swish(self, x: float, beta: float = 1.0) -> float:
        """Swish activation: x * sigmoid(beta * x)"""
        return x * self.sigmoid(beta * x)

    def softplus(self, x: float) -> float:
        """Softplus: log(1 + e^x) - smooth approximation of ReLU"""
        if x > 20:
            return x  # Avoid overflow
        return math.log(1 + math.exp(x))

    def softmax(self, x: List[float]) -> List[float]:
        """Softmax function for probability distribution"""
        max_x = max(x)  # Numerical stability
        exp_x = [math.exp(xi - max_x) for xi in x]
        sum_exp = sum(exp_x)
        return [e / sum_exp for e in exp_x]

    def log_softmax(self, x: List[float]) -> List[float]:
        """Log-softmax for numerical stability"""
        max_x = max(x)
        log_sum_exp = max_x + math.log(sum(math.exp(xi - max_x) for xi in x))
        return [xi - log_sum_exp for xi in x]

    # ==========================================
    # LOSS FUNCTIONS
    # ==========================================

    def mse_loss(self, y_true: List[float], y_pred: List[float]) -> float:
        """Mean Squared Error loss"""
        n = len(y_true)
        return sum((t - p) ** 2 for t, p in zip(y_true, y_pred)) / n

    def mse_gradient(self, y_true: List[float], y_pred: List[float]) -> List[float]:
        """Gradient of MSE loss with respect to predictions"""
        n = len(y_true)
        return [2 * (p - t) / n for t, p in zip(y_true, y_pred)]

    def mae_loss(self, y_true: List[float], y_pred: List[float]) -> float:
        """Mean Absolute Error loss"""
        n = len(y_true)
        return sum(abs(t - p) for t, p in zip(y_true, y_pred)) / n

    def huber_loss(self, y_true: List[float], y_pred: List[float], delta: float = 1.0) -> float:
        """Huber loss - less sensitive to outliers than MSE"""
        n = len(y_true)
        total = 0.0
        for t, p in zip(y_true, y_pred):
            error = abs(t - p)
            if error <= delta:
                total += 0.5 * error ** 2
            else:
                total += delta * error - 0.5 * delta ** 2
        return total / n

    def binary_cross_entropy(self, y_true: List[float], y_pred: List[float],
                             epsilon: float = 1e-15) -> float:
        """Binary Cross-Entropy loss"""
        n = len(y_true)
        total = 0.0
        for t, p in zip(y_true, y_pred):
            p = max(epsilon, min(1 - epsilon, p))  # Clip for numerical stability
            total += -(t * math.log(p) + (1 - t) * math.log(1 - p))
        return total / n

    def categorical_cross_entropy(self, y_true: List[List[float]],
                                  y_pred: List[List[float]],
                                  epsilon: float = 1e-15) -> float:
        """Categorical Cross-Entropy loss (for multi-class)"""
        n = len(y_true)
        total = 0.0
        for true_dist, pred_dist in zip(y_true, y_pred):
            for t, p in zip(true_dist, pred_dist):
                p = max(epsilon, min(1 - epsilon, p))
                total += -t * math.log(p)
        return total / n

    def hinge_loss(self, y_true: List[float], y_pred: List[float]) -> float:
        """Hinge loss for SVM (y_true should be -1 or 1)"""
        n = len(y_true)
        return sum(max(0, 1 - t * p) for t, p in zip(y_true, y_pred)) / n

    def focal_loss(self, y_true: List[float], y_pred: List[float],
                   gamma: float = 2.0, alpha: float = 0.25,
                   epsilon: float = 1e-15) -> float:
        """Focal loss - handles class imbalance"""
        n = len(y_true)
        total = 0.0
        for t, p in zip(y_true, y_pred):
            p = max(epsilon, min(1 - epsilon, p))
            if t == 1:
                total += -alpha * (1 - p) ** gamma * math.log(p)
            else:
                total += -(1 - alpha) * p ** gamma * math.log(1 - p)
        return total / n

    # ==========================================
    # KERNEL FUNCTIONS
    # ==========================================

    def linear_kernel(self, x: List[float], y: List[float]) -> float:
        """Linear kernel: K(x,y) = x · y"""
        return sum(xi * yi for xi, yi in zip(x, y))

    def polynomial_kernel(self, x: List[float], y: List[float],
                          degree: int = 3, gamma: float = 1.0,
                          coef0: float = 1.0) -> float:
        """Polynomial kernel: K(x,y) = (gamma * x·y + coef0)^degree"""
        dot = sum(xi * yi for xi, yi in zip(x, y))
        return (gamma * dot + coef0) ** degree

    def rbf_kernel(self, x: List[float], y: List[float],
                   gamma: float = 1.0) -> float:
        """RBF (Gaussian) kernel: K(x,y) = exp(-gamma * ||x-y||^2)"""
        sq_dist = sum((xi - yi) ** 2 for xi, yi in zip(x, y))
        return math.exp(-gamma * sq_dist)

    def sigmoid_kernel(self, x: List[float], y: List[float],
                       gamma: float = 1.0, coef0: float = 0.0) -> float:
        """Sigmoid kernel: K(x,y) = tanh(gamma * x·y + coef0)"""
        dot = sum(xi * yi for xi, yi in zip(x, y))
        return math.tanh(gamma * dot + coef0)

    def laplacian_kernel(self, x: List[float], y: List[float],
                         gamma: float = 1.0) -> float:
        """Laplacian kernel: K(x,y) = exp(-gamma * ||x-y||_1)"""
        l1_dist = sum(abs(xi - yi) for xi, yi in zip(x, y))
        return math.exp(-gamma * l1_dist)

    def cosine_kernel(self, x: List[float], y: List[float]) -> float:
        """Cosine similarity kernel"""
        dot = sum(xi * yi for xi, yi in zip(x, y))
        norm_x = math.sqrt(sum(xi ** 2 for xi in x))
        norm_y = math.sqrt(sum(yi ** 2 for yi in y))
        if norm_x == 0 or norm_y == 0:
            return 0.0
        return dot / (norm_x * norm_y)

    def chi_squared_kernel(self, x: List[float], y: List[float]) -> float:
        """Chi-squared kernel for histograms"""
        total = 0.0
        for xi, yi in zip(x, y):
            if xi + yi != 0:
                total += 2 * xi * yi / (xi + yi)
        return total

    def compute_kernel_matrix(self, X: List[List[float]],
                              kernel_func: Callable,
                              **kwargs) -> List[List[float]]:
        """Compute Gram matrix for a set of points"""
        n = len(X)
        K = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i, n):
                k_ij = kernel_func(X[i], X[j], **kwargs)
                K[i][j] = k_ij
                K[j][i] = k_ij
        return K

    # ==========================================
    # OPTIMIZATION ALGORITHMS
    # ==========================================

    def sgd_step(self, params: List[float], grads: List[float],
                 lr: float = 0.01) -> List[float]:
        """Stochastic Gradient Descent update"""
        return [p - lr * g for p, g in zip(params, grads)]

    def momentum_step(self, params: List[float], grads: List[float],
                      velocity: List[float], lr: float = 0.01,
                      momentum: float = 0.9) -> Tuple[List[float], List[float]]:
        """SGD with Momentum update"""
        new_velocity = [momentum * v + g for v, g in zip(velocity, grads)]
        new_params = [p - lr * v for p, v in zip(params, new_velocity)]
        return new_params, new_velocity

    def nesterov_step(self, params: List[float], grads: List[float],
                      velocity: List[float], lr: float = 0.01,
                      momentum: float = 0.9) -> Tuple[List[float], List[float]]:
        """Nesterov Accelerated Gradient update"""
        new_velocity = [momentum * v + g for v, g in zip(velocity, grads)]
        new_params = [p - lr * (momentum * v_new + g)
                     for p, v_new, g in zip(params, new_velocity, grads)]
        return new_params, new_velocity

    def adagrad_step(self, params: List[float], grads: List[float],
                     cache: List[float], lr: float = 0.01,
                     epsilon: float = 1e-8) -> Tuple[List[float], List[float]]:
        """AdaGrad update"""
        new_cache = [c + g ** 2 for c, g in zip(cache, grads)]
        new_params = [p - lr * g / (math.sqrt(c) + epsilon)
                     for p, g, c in zip(params, grads, new_cache)]
        return new_params, new_cache

    def rmsprop_step(self, params: List[float], grads: List[float],
                     cache: List[float], lr: float = 0.001,
                     decay: float = 0.9, epsilon: float = 1e-8) -> Tuple[List[float], List[float]]:
        """RMSprop update"""
        new_cache = [decay * c + (1 - decay) * g ** 2
                    for c, g in zip(cache, grads)]
        new_params = [p - lr * g / (math.sqrt(c) + epsilon)
                     for p, g, c in zip(params, grads, new_cache)]
        return new_params, new_cache

    def adam_step(self, params: List[float], grads: List[float],
                  m: List[float], v: List[float], t: int,
                  lr: float = 0.001, beta1: float = 0.9,
                  beta2: float = 0.999, epsilon: float = 1e-8) -> Tuple[List[float], List[float], List[float]]:
        """Adam optimizer update"""
        # Update biased first moment estimate
        new_m = [beta1 * mi + (1 - beta1) * g for mi, g in zip(m, grads)]
        # Update biased second raw moment estimate
        new_v = [beta2 * vi + (1 - beta2) * g ** 2 for vi, g in zip(v, grads)]
        # Bias correction
        m_hat = [mi / (1 - beta1 ** t) for mi in new_m]
        v_hat = [vi / (1 - beta2 ** t) for vi in new_v]
        # Update parameters
        new_params = [p - lr * mh / (math.sqrt(vh) + epsilon)
                     for p, mh, vh in zip(params, m_hat, v_hat)]
        return new_params, new_m, new_v

    def adamw_step(self, params: List[float], grads: List[float],
                   m: List[float], v: List[float], t: int,
                   lr: float = 0.001, beta1: float = 0.9,
                   beta2: float = 0.999, epsilon: float = 1e-8,
                   weight_decay: float = 0.01) -> Tuple[List[float], List[float], List[float]]:
        """AdamW optimizer update (Adam with decoupled weight decay)"""
        # Update biased moment estimates
        new_m = [beta1 * mi + (1 - beta1) * g for mi, g in zip(m, grads)]
        new_v = [beta2 * vi + (1 - beta2) * g ** 2 for vi, g in zip(v, grads)]
        # Bias correction
        m_hat = [mi / (1 - beta1 ** t) for mi in new_m]
        v_hat = [vi / (1 - beta2 ** t) for vi in new_v]
        # Update with decoupled weight decay
        new_params = [p * (1 - lr * weight_decay) - lr * mh / (math.sqrt(vh) + epsilon)
                     for p, mh, vh in zip(params, m_hat, v_hat)]
        return new_params, new_m, new_v

    def lamb_step(self, params: List[float], grads: List[float],
                  m: List[float], v: List[float], t: int,
                  lr: float = 0.001, beta1: float = 0.9,
                  beta2: float = 0.999, epsilon: float = 1e-6,
                  weight_decay: float = 0.01) -> Tuple[List[float], List[float], List[float]]:
        """LAMB optimizer (Layer-wise Adaptive Moments for Batch training)"""
        # Adam moment updates
        new_m = [beta1 * mi + (1 - beta1) * g for mi, g in zip(m, grads)]
        new_v = [beta2 * vi + (1 - beta2) * g ** 2 for vi, g in zip(v, grads)]
        # Bias correction
        m_hat = [mi / (1 - beta1 ** t) for mi in new_m]
        v_hat = [vi / (1 - beta2 ** t) for vi in new_v]
        # Compute Adam update
        adam_update = [mh / (math.sqrt(vh) + epsilon) + weight_decay * p
                      for mh, vh, p in zip(m_hat, v_hat, params)]
        # Compute trust ratio
        param_norm = math.sqrt(sum(p ** 2 for p in params))
        update_norm = math.sqrt(sum(u ** 2 for u in adam_update))
        if param_norm > 0 and update_norm > 0:
            trust_ratio = param_norm / update_norm
        else:
            trust_ratio = 1.0
        # Update parameters
        new_params = [p - lr * trust_ratio * u
                     for p, u in zip(params, adam_update)]
        return new_params, new_m, new_v

    # ==========================================
    # INFORMATION THEORY
    # ==========================================

    def entropy(self, probs: List[float], base: float = math.e) -> float:
        """Shannon entropy: H(X) = -sum(p * log(p))"""
        total = 0.0
        for p in probs:
            if p > 0:
                total -= p * math.log(p) / math.log(base)
        return total

    def cross_entropy(self, p: List[float], q: List[float],
                      epsilon: float = 1e-15) -> float:
        """Cross-entropy: H(p,q) = -sum(p * log(q))"""
        total = 0.0
        for pi, qi in zip(p, q):
            qi = max(epsilon, qi)
            if pi > 0:
                total -= pi * math.log(qi)
        return total

    def kl_divergence(self, p: List[float], q: List[float],
                      epsilon: float = 1e-15) -> float:
        """Kullback-Leibler divergence: D_KL(P||Q) = sum(p * log(p/q))"""
        total = 0.0
        for pi, qi in zip(p, q):
            qi = max(epsilon, qi)
            if pi > 0:
                total += pi * math.log(pi / qi)
        return total

    def js_divergence(self, p: List[float], q: List[float]) -> float:
        """Jensen-Shannon divergence (symmetric version of KL)"""
        m = [(pi + qi) / 2 for pi, qi in zip(p, q)]
        return (self.kl_divergence(p, m) + self.kl_divergence(q, m)) / 2

    def mutual_information(self, joint_probs: List[List[float]]) -> float:
        """Mutual information I(X;Y) from joint probability matrix"""
        rows = len(joint_probs)
        cols = len(joint_probs[0]) if rows > 0 else 0

        # Marginals
        p_x = [sum(joint_probs[i][j] for j in range(cols)) for i in range(rows)]
        p_y = [sum(joint_probs[i][j] for i in range(rows)) for j in range(cols)]

        # Compute MI
        mi = 0.0
        for i in range(rows):
            for j in range(cols):
                if joint_probs[i][j] > 0 and p_x[i] > 0 and p_y[j] > 0:
                    mi += joint_probs[i][j] * math.log(
                        joint_probs[i][j] / (p_x[i] * p_y[j])
                    )
        return mi

    def conditional_entropy(self, joint_probs: List[List[float]]) -> float:
        """Conditional entropy H(Y|X)"""
        rows = len(joint_probs)
        cols = len(joint_probs[0]) if rows > 0 else 0

        p_x = [sum(joint_probs[i][j] for j in range(cols)) for i in range(rows)]

        h_y_given_x = 0.0
        for i in range(rows):
            if p_x[i] > 0:
                for j in range(cols):
                    p_y_given_x = joint_probs[i][j] / p_x[i] if p_x[i] > 0 else 0
                    if p_y_given_x > 0:
                        h_y_given_x -= joint_probs[i][j] * math.log(p_y_given_x)
        return h_y_given_x

    # ==========================================
    # MATRIX CALCULUS
    # ==========================================

    def gradient_numerical(self, f: Callable[[List[float]], float],
                           x: List[float], epsilon: float = 1e-5) -> List[float]:
        """Numerical gradient using central differences"""
        grad = []
        for i in range(len(x)):
            x_plus = x.copy()
            x_minus = x.copy()
            x_plus[i] += epsilon
            x_minus[i] -= epsilon
            grad.append((f(x_plus) - f(x_minus)) / (2 * epsilon))
        return grad

    def jacobian_numerical(self, f: Callable[[List[float]], List[float]],
                           x: List[float], epsilon: float = 1e-5) -> List[List[float]]:
        """Numerical Jacobian matrix"""
        f_x = f(x)
        m = len(f_x)
        n = len(x)
        jacobian = [[0.0] * n for _ in range(m)]

        for j in range(n):
            x_plus = x.copy()
            x_minus = x.copy()
            x_plus[j] += epsilon
            x_minus[j] -= epsilon
            f_plus = f(x_plus)
            f_minus = f(x_minus)
            for i in range(m):
                jacobian[i][j] = (f_plus[i] - f_minus[i]) / (2 * epsilon)
        return jacobian

    def hessian_numerical(self, f: Callable[[List[float]], float],
                          x: List[float], epsilon: float = 1e-5) -> List[List[float]]:
        """Numerical Hessian matrix"""
        n = len(x)
        hessian = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(i, n):
                x_pp = x.copy()
                x_pm = x.copy()
                x_mp = x.copy()
                x_mm = x.copy()

                x_pp[i] += epsilon
                x_pp[j] += epsilon
                x_pm[i] += epsilon
                x_pm[j] -= epsilon
                x_mp[i] -= epsilon
                x_mp[j] += epsilon
                x_mm[i] -= epsilon
                x_mm[j] -= epsilon

                h_ij = (f(x_pp) - f(x_pm) - f(x_mp) + f(x_mm)) / (4 * epsilon ** 2)
                hessian[i][j] = h_ij
                hessian[j][i] = h_ij

        return hessian

    def check_gradient(self, analytical_grad: List[float],
                       numerical_grad: List[float],
                       tolerance: float = 1e-5) -> Dict:
        """Verify analytical gradient against numerical approximation"""
        diff = [abs(a - n) for a, n in zip(analytical_grad, numerical_grad)]
        max_diff = max(diff)
        avg_diff = sum(diff) / len(diff)

        # Relative error
        rel_errors = []
        for a, n in zip(analytical_grad, numerical_grad):
            denom = max(abs(a), abs(n), 1e-10)
            rel_errors.append(abs(a - n) / denom)
        max_rel_error = max(rel_errors)

        return {
            'passed': max_rel_error < tolerance,
            'max_diff': max_diff,
            'avg_diff': avg_diff,
            'max_relative_error': max_rel_error,
            'element_diffs': diff
        }

    # ==========================================
    # DIMENSIONALITY REDUCTION
    # ==========================================

    def center_data(self, X: List[List[float]]) -> Tuple[List[List[float]], List[float]]:
        """Center data by subtracting mean"""
        n = len(X)
        if n == 0:
            return X, []
        d = len(X[0])

        # Compute mean
        mean = [sum(X[i][j] for i in range(n)) / n for j in range(d)]

        # Center
        centered = [[X[i][j] - mean[j] for j in range(d)] for i in range(n)]
        return centered, mean

    def covariance_matrix(self, X: List[List[float]]) -> List[List[float]]:
        """Compute covariance matrix"""
        centered, _ = self.center_data(X)
        n = len(centered)
        if n == 0:
            return []
        d = len(centered[0])

        cov = [[0.0] * d for _ in range(d)]
        for i in range(d):
            for j in range(i, d):
                c_ij = sum(centered[k][i] * centered[k][j] for k in range(n)) / (n - 1)
                cov[i][j] = c_ij
                cov[j][i] = c_ij
        return cov

    def power_iteration(self, A: List[List[float]],
                        num_iterations: int = 100,
                        tolerance: float = 1e-10) -> Tuple[float, List[float]]:
        """Power iteration to find dominant eigenvalue/eigenvector"""
        n = len(A)
        # Random initial vector
        b = [1.0 / math.sqrt(n)] * n

        for _ in range(num_iterations):
            # Matrix-vector product
            Ab = [sum(A[i][j] * b[j] for j in range(n)) for i in range(n)]
            # Compute eigenvalue
            eigenvalue = sum(Ab[i] * b[i] for i in range(n))
            # Normalize
            norm = math.sqrt(sum(x ** 2 for x in Ab))
            if norm < tolerance:
                break
            b_new = [x / norm for x in Ab]
            # Check convergence
            diff = sum((b_new[i] - b[i]) ** 2 for i in range(n))
            b = b_new
            if diff < tolerance:
                break

        return eigenvalue, b

    def pca_simple(self, X: List[List[float]],
                   n_components: int = 2) -> Dict:
        """Simple PCA implementation using power iteration"""
        centered, mean = self.center_data(X)
        cov = self.covariance_matrix(X)

        n = len(cov)
        components = []
        eigenvalues = []
        A = [row.copy() for row in cov]

        for _ in range(min(n_components, n)):
            eigenvalue, eigenvector = self.power_iteration(A)
            eigenvalues.append(eigenvalue)
            components.append(eigenvector)

            # Deflate matrix
            for i in range(n):
                for j in range(n):
                    A[i][j] -= eigenvalue * eigenvector[i] * eigenvector[j]

        # Project data
        projected = []
        for point in centered:
            proj = [sum(point[j] * components[k][j] for j in range(n))
                   for k in range(len(components))]
            projected.append(proj)

        # Explained variance ratio
        total_var = sum(cov[i][i] for i in range(n))
        explained_variance_ratio = [ev / total_var if total_var > 0 else 0
                                   for ev in eigenvalues]

        return {
            'components': components,
            'eigenvalues': eigenvalues,
            'explained_variance_ratio': explained_variance_ratio,
            'transformed': projected,
            'mean': mean
        }

    def svd_simple(self, A: List[List[float]],
                   k: int = None) -> Dict:
        """Simplified SVD using power iteration on A^T A"""
        m, n = len(A), len(A[0]) if A else 0
        if k is None:
            k = min(m, n)

        # Compute A^T A
        AtA = [[sum(A[r][i] * A[r][j] for r in range(m))
               for j in range(n)] for i in range(n)]

        # Get top k right singular vectors (V)
        V = []
        singular_values = []
        B = [row.copy() for row in AtA]

        for _ in range(min(k, n)):
            eigenvalue, eigenvector = self.power_iteration(B)
            singular_value = math.sqrt(max(0, eigenvalue))
            singular_values.append(singular_value)
            V.append(eigenvector)

            # Deflate
            for i in range(n):
                for j in range(n):
                    B[i][j] -= eigenvalue * eigenvector[i] * eigenvector[j]

        # Compute U = A V / sigma
        U = []
        for idx, (v, s) in enumerate(zip(V, singular_values)):
            if s > 1e-10:
                u = [sum(A[i][j] * v[j] for j in range(n)) / s for i in range(m)]
            else:
                u = [0.0] * m
            U.append(u)

        return {
            'U': U,  # Left singular vectors (as rows)
            'S': singular_values,
            'V': V   # Right singular vectors (as rows)
        }

    # ==========================================
    # REGULARIZATION
    # ==========================================

    def l1_penalty(self, weights: List[float], lambda_: float = 0.01) -> float:
        """L1 regularization (Lasso): lambda * sum(|w|)"""
        return lambda_ * sum(abs(w) for w in weights)

    def l1_gradient(self, weights: List[float], lambda_: float = 0.01) -> List[float]:
        """Gradient of L1 penalty (subgradient at 0)"""
        return [lambda_ * (1 if w > 0 else -1 if w < 0 else 0) for w in weights]

    def l2_penalty(self, weights: List[float], lambda_: float = 0.01) -> float:
        """L2 regularization (Ridge): lambda * sum(w^2) / 2"""
        return lambda_ * sum(w ** 2 for w in weights) / 2

    def l2_gradient(self, weights: List[float], lambda_: float = 0.01) -> List[float]:
        """Gradient of L2 penalty"""
        return [lambda_ * w for w in weights]

    def elastic_net_penalty(self, weights: List[float],
                            lambda_: float = 0.01,
                            l1_ratio: float = 0.5) -> float:
        """Elastic Net: l1_ratio * L1 + (1 - l1_ratio) * L2"""
        l1 = self.l1_penalty(weights, lambda_)
        l2 = self.l2_penalty(weights, lambda_)
        return l1_ratio * l1 + (1 - l1_ratio) * l2

    def dropout_mask(self, size: int, p: float = 0.5,
                     training: bool = True) -> List[float]:
        """Generate dropout mask (simplified - requires randomness in practice)"""
        if not training:
            return [1.0] * size
        # During training, scale by 1/(1-p) to maintain expected values
        scale = 1.0 / (1 - p) if p < 1 else 0
        # This is a placeholder - in practice, use random selection
        return [scale] * size

    # ==========================================
    # NEURAL NETWORK LAYERS (MATH ONLY)
    # ==========================================

    def linear_forward(self, x: List[float], W: List[List[float]],
                       b: List[float]) -> List[float]:
        """Linear layer forward: y = Wx + b"""
        out_dim = len(W)
        return [sum(W[i][j] * x[j] for j in range(len(x))) + b[i]
               for i in range(out_dim)]

    def linear_backward(self, x: List[float], W: List[List[float]],
                        grad_output: List[float]) -> Dict:
        """Linear layer backward pass"""
        in_dim = len(x)
        out_dim = len(W)

        # Gradient w.r.t. W: outer product of grad_output and x
        grad_W = [[grad_output[i] * x[j] for j in range(in_dim)]
                 for i in range(out_dim)]

        # Gradient w.r.t. b
        grad_b = grad_output.copy()

        # Gradient w.r.t. x
        grad_x = [sum(W[i][j] * grad_output[i] for i in range(out_dim))
                 for j in range(in_dim)]

        return {'grad_W': grad_W, 'grad_b': grad_b, 'grad_x': grad_x}

    def batch_norm_forward(self, x: List[float], gamma: float = 1.0,
                           beta: float = 0.0, epsilon: float = 1e-5) -> Dict:
        """Batch normalization (single sample simplified)"""
        mean = sum(x) / len(x)
        var = sum((xi - mean) ** 2 for xi in x) / len(x)
        std = math.sqrt(var + epsilon)
        x_norm = [(xi - mean) / std for xi in x]
        out = [gamma * xn + beta for xn in x_norm]

        return {
            'output': out,
            'x_norm': x_norm,
            'mean': mean,
            'var': var,
            'std': std
        }

    def layer_norm_forward(self, x: List[float], gamma: List[float] = None,
                           beta: List[float] = None, epsilon: float = 1e-5) -> List[float]:
        """Layer normalization"""
        mean = sum(x) / len(x)
        var = sum((xi - mean) ** 2 for xi in x) / len(x)
        std = math.sqrt(var + epsilon)
        x_norm = [(xi - mean) / std for xi in x]

        if gamma is None:
            gamma = [1.0] * len(x)
        if beta is None:
            beta = [0.0] * len(x)

        return [g * xn + b for g, xn, b in zip(gamma, x_norm, beta)]

    # ==========================================
    # ATTENTION MECHANISM MATH
    # ==========================================

    def scaled_dot_product_attention(self, Q: List[List[float]],
                                     K: List[List[float]],
                                     V: List[List[float]],
                                     mask: List[List[float]] = None) -> List[List[float]]:
        """Scaled dot-product attention: softmax(QK^T / sqrt(d_k)) V"""
        d_k = len(K[0]) if K else 1
        scale = math.sqrt(d_k)

        # Compute attention scores: Q K^T
        n_q = len(Q)
        n_k = len(K)
        scores = [[sum(Q[i][d] * K[j][d] for d in range(d_k)) / scale
                  for j in range(n_k)] for i in range(n_q)]

        # Apply mask if provided (set masked positions to -inf)
        if mask:
            for i in range(n_q):
                for j in range(n_k):
                    if mask[i][j] == 0:
                        scores[i][j] = -float('inf')

        # Softmax along K dimension
        attention_weights = [self.softmax(scores[i]) for i in range(n_q)]

        # Weighted sum of V
        d_v = len(V[0]) if V else 0
        output = [[sum(attention_weights[i][j] * V[j][d] for j in range(n_k))
                  for d in range(d_v)] for i in range(n_q)]

        return output

    def positional_encoding(self, max_len: int, d_model: int) -> List[List[float]]:
        """Sinusoidal positional encoding for transformers"""
        pe = [[0.0] * d_model for _ in range(max_len)]

        for pos in range(max_len):
            for i in range(0, d_model, 2):
                angle = pos / (10000 ** (i / d_model))
                pe[pos][i] = math.sin(angle)
                if i + 1 < d_model:
                    pe[pos][i + 1] = math.cos(angle)

        return pe

    # ==========================================
    # METRIC LEARNING
    # ==========================================

    def euclidean_distance(self, x: List[float], y: List[float]) -> float:
        """Euclidean (L2) distance"""
        return math.sqrt(sum((xi - yi) ** 2 for xi, yi in zip(x, y)))

    def manhattan_distance(self, x: List[float], y: List[float]) -> float:
        """Manhattan (L1) distance"""
        return sum(abs(xi - yi) for xi, yi in zip(x, y))

    def cosine_distance(self, x: List[float], y: List[float]) -> float:
        """Cosine distance: 1 - cosine_similarity"""
        return 1 - self.cosine_kernel(x, y)

    def mahalanobis_distance(self, x: List[float], y: List[float],
                             cov_inv: List[List[float]]) -> float:
        """Mahalanobis distance with inverse covariance matrix"""
        diff = [xi - yi for xi, yi in zip(x, y)]
        n = len(diff)
        # d^T * cov_inv * d
        temp = [sum(cov_inv[i][j] * diff[j] for j in range(n)) for i in range(n)]
        return math.sqrt(sum(diff[i] * temp[i] for i in range(n)))

    def triplet_loss(self, anchor: List[float], positive: List[float],
                     negative: List[float], margin: float = 1.0) -> float:
        """Triplet loss for metric learning"""
        d_pos = self.euclidean_distance(anchor, positive)
        d_neg = self.euclidean_distance(anchor, negative)
        return max(0, d_pos - d_neg + margin)

    def contrastive_loss(self, x1: List[float], x2: List[float],
                         label: int, margin: float = 1.0) -> float:
        """Contrastive loss: label=1 for similar, label=0 for dissimilar"""
        d = self.euclidean_distance(x1, x2)
        if label == 1:
            return d ** 2
        else:
            return max(0, margin - d) ** 2


# Singleton instance
ml = MLMath()
