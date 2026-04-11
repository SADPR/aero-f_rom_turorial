#!/usr/bin/env python3

import argparse
import sys
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel
from sklearn.metrics import mean_squared_error
import time

########################################
# Main script
########################################
def main():
    parser = argparse.ArgumentParser(
        description="Train a GaussianProcessRegressor for PROM, using standardized input & output."
    )
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
    q_s = raw[:, args.input_size: args.input_size + args.output_size]

    # 3) Compute min & max for input and output
    scalingMethod = 1 #0 if we were doing standard
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

    # 5) Train/val split on the scaled data
    X_train, X_val, Y_train, Y_val = train_test_split(X, Y, test_size=0.2, random_state=42)

    # ---- Measure training time ----
    start_time = time.time()

    # 6) Define GP kernel with optimized length scale
    kernel = ConstantKernel(1.0, (1e-3, 1e3)) * Matern(length_scale=1.0, length_scale_bounds=(1e-3, 1e3), nu=1.5)
    
    # Uncomment the following line to **add WhiteKernel (observation noise)**
    # kernel += WhiteKernel(noise_level=1e-5, noise_level_bounds=(1e-5, 1e-1))

    gp = GaussianProcessRegressor(kernel=kernel, alpha=1e-8, n_restarts_optimizer=4)
    gp.fit(X_train, Y_train)

    end_time = time.time()
    total_time = end_time - start_time
    print(f'Training complete! Total training time: {total_time:.2f} seconds')

    # Evaluate validation error
    Y_val_pred = gp.predict(X_val)
    val_mse = mean_squared_error(Y_val, Y_val_pred)
    val_rel = np.linalg.norm(Y_val_pred - Y_val) / np.linalg.norm(Y_val)
    print(f"[Info] Validation MSE={val_mse:.4e}, relative err={val_rel:.4e}")

    # 7) Extract GP model parameters
    alpha_ = gp.alpha_
    hyperparams = gp.kernel_.get_params()
    cval = hyperparams.get("k1__constant_value", 1.0)
    length_scale = hyperparams.get("k2__length_scale", 1.0)
    length_scale = np.atleast_1d(length_scale)  # Ensure it's an array

    # 8) Save model data to ASCII files
    # Save alpha_ => "gp_precomputations.txt"
    with open("gp_precomputations.txt", "w") as f:
        f.write(f"{alpha_.shape[0]} {alpha_.shape[1]}\n")
        np.savetxt(f, alpha_, fmt="%.7f")

    # Save X_train => "gp_xTrain.txt"
    with open("gp_xTrain.txt", "w") as f:
        f.write(f"{X_train.shape[0]} {X_train.shape[1]}\n")
        np.savetxt(f, X_train, fmt="%.7f")

    with open("gp_stdscaling.txt", "w") as f:
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

    # Save hyperparameters => "gp_hyper.txt"
    with open("gp_hyper.txt", "w") as f:
        nrow = 1 + length_scale.size
        f.write(f"{nrow} 1\n")
        f.write(f"{cval:.7f}\n")
        for val in length_scale:
            f.write(f"{val:.7f}\n")

    print("[Done] GP model saved to gp_precomputations.txt, gp_xTrain.txt, gp_stdscaling.txt, gp_hyper.txt.")

if __name__ == "__main__":
    main()
