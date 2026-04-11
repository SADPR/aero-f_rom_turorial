import numpy as np
import matplotlib.pyplot as plt

# Enable LaTeX rendering
plt.rcParams.update({
    'text.usetex': True,
    'font.family': 'serif',
    'axes.titlesize': 10,
    'axes.labelsize': 10,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 8,
    'figure.autolayout': True,
    'figure.subplot.left': 0.05,
    'figure.subplot.right': 0.95,
    'figure.subplot.top': 0.95,
    'figure.subplot.bottom': 0.05
})

def read_inputs_and_labels():
    """Defines the directories and labels internally."""
    return [
        ('../run.fom/postpro', 'HDM'),
        ('postpro', 'PROM-RBF 35')
    ]

def load_data(filename, final_time):
    """Loads data from a text file and filters by final time."""
    data = np.loadtxt(filename)
    return data[data[:, 1] <= final_time, :]

def plot_data(data_list, labels, y_index, ylabel, filename, colors, plot_index):
    """Generic function to plot data."""
    plt.figure(figsize=(8,5))
    plt.grid(True, linestyle='--', alpha=0.7)
    for i in plot_index:
        plt.plot(data_list[i][:,1], data_list[i][:,y_index], colors[i], label=labels[i])
    plt.xlabel(r'$t$')
    plt.ylabel(ylabel)
    plt.legend(loc='upper left')
    plt.savefig(f'{filename}.pdf')
    plt.close()

def main():
    final_time = 150  # Define the final time here
    plot_index = [0, 1]  # Define which datasets to plot
    
    dirs, labels = zip(*read_inputs_and_labels())
    
    # Define colors for each model type
    color_map = {
        'HDM': 'k-',
        'PROM-RBF 35': 'b-',
    }
    colors = [color_map[label] for label in labels]
    
    # Load datasets
    lift_drag_data = [load_data(f'{d}/LiftandDrag.out', final_time) for d in dirs]
    velocity_data = [load_data(f'{d}/ProbeVelocity.out', final_time) for d in dirs]
    
    # Plot selected data
    plot_data(lift_drag_data, labels, 4, r'Drag', 'drag_plot', colors, plot_index)
    plot_data(lift_drag_data, labels, 6, r'Lift', 'lift_plot', colors, plot_index)
    plot_data(velocity_data, labels, 2, r'x-velocity', 'x_velocity_plot', colors, plot_index)
    plot_data(velocity_data, labels, 4, r'z-velocity', 'z_velocity_plot', colors, plot_index)
    
    print("Plots saved as PDFs.")

if __name__ == "__main__":
    main()
