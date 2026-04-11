#!/usr/bin/env python3

import argparse
import numpy as np
import sys
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import time

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
    'imq': inverse_multiquadric_rbf,
    'multiquadric': multiquadric_rbf,
    'linear': linear_rbf
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

    #
    # 3) Use the OLD approach: single pass over all columns
    #
    #    i.e., we treat raw as shape (nSamples, input_size+output_size)
    #    compute mu_all, std_all from raw, then slice out mu_in, sig_in, etc.
    #
    scalingMethod = 0#1 if doing min max 
    mu_all = np.mean(raw, axis=0)  # shape = (input_size+output_size,)
    std_all = np.std(raw, axis=0)  # shape = (input_size+output_size,)

    mu_in = mu_all[:args.input_size]
    sig_in = std_all[:args.input_size]
    mu_out = mu_all[args.input_size : args.input_size + args.output_size]
    sig_out = std_all[args.input_size : args.input_size + args.output_size]

    #
    # 4) Standardize input & output using the lumps approach
    #
    X = (q_p - mu_in) / sig_in
    Y = (q_s - mu_out) / sig_out
    
    # 5) Train/val split
    X_train, X_val, Y_train, Y_val = train_test_split(X, Y, test_size=0.2, random_state=42)

    # 6) Grid-search over epsilon, kernel
    epsilon_values = np.logspace(np.log10(1e-4), np.log10(10), 50)
    kernel_names = list(rbf_kernels.keys())

    best_eps, best_kernel, best_err, best_W = None, None, 1e12, None

    # ---- Measure training time ----
    start_time = time.time()
    dists_train = np.linalg.norm(X_train[:, np.newaxis, :] - X_train[np.newaxis, :, :], axis=2)
    pairwise_dists = dists_train[np.triu_indices(len(X_train), k=1)]

    char_dist = np.median(pairwise_dists)  # or percentile, or mean
    eps_min = 0.5 / char_dist
    eps_max = 5.0  / char_dist

    print(f"Recommended epsilon range ~ [{eps_min:.3g}, {eps_max:.3g}]")
    max_dist = np.max(dists_train)
    print("Max distance among training points in standardized space:", max_dist)
    print("Grid search over epsilon and kernel...")
    for eps in epsilon_values:
        for kn in kernel_names:
            kernel_func = rbf_kernels[kn]

            # Compute pairwise distances for training set
            Phi_train = kernel_func(dists_train, eps)
            Phi_train += 1e-8 * np.eye(len(X_train))  # Regularization

            try:
                W = np.linalg.solve(Phi_train, Y_train)
            except np.linalg.LinAlgError:
                print(f"LinAlgError at eps={eps}, kernel={kn}, skipping.")
                continue

            # Validation set
            dists_val = np.linalg.norm(X_val[:, np.newaxis, :] - X_train[np.newaxis, :, :], axis=2)
            Phi_val = kernel_func(dists_val, eps)
            Y_val_pred = Phi_val @ W
            mse = mean_squared_error(Y_val, Y_val_pred)
            re = np.linalg.norm(Y_val-Y_val_pred)/np.linalg.norm(Y_val)*100
            print(f"eps={eps:.5g}, kernel={kn}, val MSE={mse:e}, val RE={re:.2}%")

            if mse < best_err:
                best_err = mse
                best_eps = eps
                best_kernel = kn
                best_W = W.copy()

    if best_W is None:
        print("[Error] No feasible solution found in grid search. Exiting.")
        return

    print(f"[Best] kernel={best_kernel}, eps={best_eps}, val MSE={best_err:e}")

    # 7) Retrain on full dataset
    dists_all = np.linalg.norm(X[:, np.newaxis, :] - X[np.newaxis, :, :], axis=2)
    Phi_all = rbf_kernels[best_kernel](dists_all, best_eps)
    Phi_all += 1e-8 * np.eye(len(X))

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
        np.savetxt(f, mu_in[None, :], fmt="%.7f")
        np.savetxt(f, sig_in[None, :], fmt="%.7f")
        np.savetxt(f, mu_out[None, :], fmt="%.7f")
        np.savetxt(f, sig_out[None, :], fmt="%.7f")

    with open("rbf_hyper.txt", "w") as f:
        # We continue writing "2 1" lines: kernel name + epsilon
        f.write(f"2 1\n")
        f.write(f"{best_kernel}\n")
        f.write(f"{best_eps:.7f}\n")

    print(f"[Done] RBF model saved with 'old-style' scaling (mu_in/out from entire row data).")

if __name__ == "__main__":
    main()

