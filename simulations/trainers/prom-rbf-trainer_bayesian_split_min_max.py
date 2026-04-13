#!/usr/bin/env python3

import argparse
import numpy as np
import sys
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import time
from skopt import gp_minimize
from skopt.space import Real, Categorical
from skopt.utils import use_named_args
from sklearn.model_selection import KFold

########################################
# RBF Kernels (Including Linear RBF)
########################################
def gaussian_rbf(r, epsilon):
    return np.exp(-(epsilon * r) ** 2)

def inverse_multiquadric_rbf(r, epsilon):
    return 1.0 / np.sqrt(1 + (epsilon * r) ** 2)

def multiquadric_rbf(r, epsilon):
    return np.sqrt(1 + (epsilon * r) ** 2)

def linear_rbf(r, epsilon):
    return r  # Linear kernel (acts as a distance metric)

rbf_kernels = {
    'gaussian': gaussian_rbf,
    'imq': inverse_multiquadric_rbf
    #'multiquadric': multiquadric_rbf,
    #'linear': linear_rbf
}

########################################
# Main script
########################################
def main():
    """
    NOTE:
    This script now uses the 'old approach' of computing mu_in, sig_in, mu_out, sig_out
    from a single pass over all columns (input + output). This may fix mismatches with
    HPC code that expects that convention.
    """

    parser = argparse.ArgumentParser(description="Train an RBF-based PROM model with standardized input/output.")
    parser.add_argument("--data_file", type=str, help="CSV with (q_p + q_s) columns.")
    parser.add_argument("--input_size", type=int, help="Number of primary coords (q_p).")
    parser.add_argument("--output_size", type=int, help="Number of secondary coords (q_s).")
    parser.add_argument("--skip_columns", type=int, default=0, help="Skip these many columns from data_file.")
    parser.add_argument("--skip_rows", type=int, default=0, help="Skip these many rows from data_file.")

    args = parser.parse_args()

    # Display a message about preprocessing the state.coords file
    print("\n[Note] Please take the 'state.coords' file and erase the first line to avoid text.")
    print("       Save the resulting file as 's.coords' before running this script.\n")

    # Set default values if no arguments are provided
    if args.data_file is None:
        args.data_file = "s.coords"
        args.input_size = 10
        args.output_size = 25
        print(f"[Info] Using default values: data_file={args.data_file}, input_size={args.input_size}, output_size={args.output_size}")

    # 1) Load data
    raw = np.loadtxt(args.data_file, skiprows=args.skip_rows, delimiter=',')
    if args.skip_columns > 0:
        raw = raw[:, args.skip_columns:]
    needed_cols = args.input_size + args.output_size
    if raw.shape[1] < needed_cols:
        print(f"[Error] Data has {raw.shape[1]} columns, need >= {needed_cols}.")
        sys.exit(1)

    print(f"[Info] Loaded data shape={raw.shape}, input_size={args.input_size}, output_size={args.output_size}")

    # 2) Separate input & output
    q_p = raw[:, :args.input_size]
    q_s = raw[:, args.input_size : args.input_size + args.output_size]

    # 3) Compute min & max for input and output
    scalingMethod = 1#0 for std
    x_min = np.min(q_p, axis=0)
    x_max = np.max(q_p, axis=0)
    y_min = np.min(q_s, axis=0)
    y_max = np.max(q_s, axis=0)

    # 4) Min–max scale each column to [-1,1]
    #    X = 2*((q_p - x_min)/(x_max - x_min)) - 1
    #    Y = 2*((q_s - y_min)/(y_max - y_min)) - 1
    denom_x = (x_max - x_min)
    denom_x[denom_x < 1e-15] = 1.0  # avoid dividing by zero if any col is constant
    denom_y = (y_max - y_min)
    denom_y[denom_y < 1e-15] = 1.0

    X = 2.0 * ((q_p - x_min) / denom_x) - 1.0
    Y = 2.0 * ((q_s - y_min) / denom_y) - 1.0

    # 5) Train/val split
    X_train, X_val, Y_train, Y_val = train_test_split(X, Y, test_size=0.2, random_state=42)

    # 6) Definition of objective function and define the search space for Bayesian optimization
    space = [
        Real(0.5, 10, name='epsilon'),
        Categorical(list(rbf_kernels.keys()), name='kernel_name'),
        Real(1e-10, 1e-8, name='lambda_val')
    ]

    # Compute distance matrix between training points
    dists_train = np.linalg.norm(
        X_train[:, np.newaxis, :] - X_train[np.newaxis, :, :], axis=2
    )

    print("Optimizing epsilon, kernel and lambda using a train–validation split and bayesian optimization...")
    # Define the objective function
    @use_named_args(space)
    def objective(epsilon, kernel_name, lambda_val):
        #epsilon = np.exp(log_epsilon)  # Optimize in log-space to ensure positivity
        kernel_func = rbf_kernels[kernel_name]
        #lambda_val = np.exp(log_lambda_val)

        # Compute kernel matrix Phi_train
        Phi_train = kernel_func(dists_train, epsilon)
        # Add regularization
        Phi_train += np.eye(Phi_train.shape[0]) * lambda_val

        # Solve for W
        try:
            W = np.linalg.solve(Phi_train, Y_train)

        except np.linalg.LinAlgError:
            print(f"LinAlgError at epsilon={epsilon:.5e}, kernel={kernel_name}. Returning infinity.")
            return np.inf  # Return infinity if matrix is singular

        # Compute distance matrix between validation and training points
        dists_val = np.linalg.norm(
            X_val[:, np.newaxis, :] - X_train[np.newaxis, :, :], axis=2
        )
        # Compute kernel matrix Phi_val
        Phi_val = kernel_func(dists_val, epsilon)

        # Predict on validation set
        y_val_pred = Phi_val @ W

        # Compute validation error
        mse_error = mean_squared_error(Y_val, y_val_pred)
        rel_error = (np.linalg.norm(Y_val - y_val_pred) / np.linalg.norm(Y_val)) * 100
        print(f"Epsilon: {epsilon:.5f}, Kernel: {kernel_name}, Lambda: {lambda_val}, "
                  f"MSE: {mse_error:.5e}, Relative Error: {rel_error:.2f}%")
        return mse_error

    # Start timing
    start_time = time.time()

    # Perform Bayesian optimization
    print("Optimizing epsilon and kernel using Bayesian optimization...")
    result = gp_minimize(
        objective,
        space,
        acq_func='EI',  # Expected Improvement
        n_calls=100,
        random_state=42,
        verbose=False,
        n_random_starts = 9
    )

    # End timing
    end_time = time.time()

    # Extract results
    best_epsilon = result.x[0]
    #best_epsilon = np.exp(best_log_epsilon)
    best_kernel_name = result.x[1]
    best_lambda_val = result.x[2]
    #best_lambda_val = np.exp(best_log_labmda_val)

    # Display results
    print(f"Best epsilon found: {best_epsilon:.5e}")
    print(f"Best kernel found: {best_kernel_name}")
    print(f"Best lambda found: {best_lambda_val}")
    print(f"Total optimization time: {end_time - start_time:.2f} seconds")

    # 7) Retrain on full dataset
    dists_all = np.linalg.norm(X[:, np.newaxis, :] - X[np.newaxis, :, :], axis=2)
    Phi_all = rbf_kernels[best_kernel_name](dists_all, best_epsilon)
    Phi_all += best_lambda_val * np.eye(len(X))

    W_final = np.linalg.solve(Phi_all, Y)
    print("Trained final W on entire dataset with best kernel & eps.")
    end_time = time.time()
    total_time = end_time - start_time
    print(f'Training complete! Total training time: {total_time:.2f} seconds')

    # 8) Save everything in a structured format
    with open("rbf_precomputations.txt", "w") as f:
        f.write(f"{W_final.shape[0]} {W_final.shape[1]}\n")
        np.savetxt(f, W_final, fmt="%.7f")

    with open("rbf_xTrain.txt", "w") as f:
        f.write(f"{X.shape[0]} {X.shape[1]}\n")
        np.savetxt(f, X, fmt="%.7f")

    with open("rbf_stdscaling.txt", "w") as f:
        # Write input_size, output_size
        f.write(f"{args.input_size} {args.output_size}\n")
        # Write scalingMethod
        f.write(str(scalingMethod) + "\n")
        # We'll store them in the same shape as previously,
        # but now each is 1 row with <input_size> or <output_size> columns.
        np.savetxt(f, x_min[None,:], fmt="%.7f")
        np.savetxt(f, x_max[None,:], fmt="%.7f")
        np.savetxt(f, y_min[None,:], fmt="%.7f")
        np.savetxt(f, y_max[None,:], fmt="%.7f")

    with open("rbf_hyper.txt", "w") as f:
        # We continue writing "2 1" lines: kernel name + epsilon
        f.write(f"2 1\n")
        f.write(f"{best_kernel_name}\n")
        f.write(f"{best_epsilon:.7f}\n")

    print(f"[Done] RBF model saved with 'old-style' scaling (mu_in/out from entire row data).")

if __name__ == "__main__":
    main()

