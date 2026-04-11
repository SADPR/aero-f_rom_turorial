import argparse
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from torch.utils.tensorboard import SummaryWriter
from matplotlib import pyplot as plt
import time  # <--- ADDED to measure training time

torch.set_default_dtype(torch.float64)


EPOCHS = 50000  # Maximum number of epochs
LR_INIT = 1e-3  # Initial learning rate for optimizer
LR_PATIENCE = 30  # How many epochs the scheduler will decrease learning rate if no improvement in test loss
COMPLETION_PATIENCE = 1000 # How many epochs with no improvement scheduler will terminate training
TRAINING_FRAC = 0.9 # fraction of input data used for training
BATCH_SIZE = 512 # Batch size of data in training 
MODEL_PATH = 'autoenc.pt' # default model output name

class TrainingMonitor:
  def __init__(self, model_path, patience, model, opt, scheduler, train=True):
    self.model_path = model_path
    self.best_crit = 1E16
    self.patience = patience
    self.its_since_improvement = 0
    self.model = model
    self.opt = opt
    self.scheduler = scheduler
    self.epoch = 0
    self.train_losses = []
    self.test_crits = []
    if train:
      self.writer = SummaryWriter()

  def check_for_completion(self, train_loss, test_crit):
    self.epoch += 1
    self.its_since_improvement += 1
    self.train_losses += [train_loss]
    self.test_crits += [test_crit]
    self.writer.add_scalar('loss/train', train_loss, self.epoch)
    self.writer.add_scalar('loss/test', test_crit, self.epoch)
    if test_crit < self.best_crit:
      self.best_crit = test_crit
      self.its_since_improvement = 0
      self.save_checkpoint()
    print('  Its since improvement: {}'.format(self.its_since_improvement))
    if self.its_since_improvement > self.patience:
      return True
    else:
      return False

  def plot_training_curves(self):
    fig_curves, ax_curves = plt.subplots()
    ax_curves.semilogy(self.test_crits, label='Test loss')
    ax_curves.semilogy(self.train_losses, label='Train loss')
    ax_curves.set_xlabel('Epoch')
    ax_curves.set_ylabel('MSE loss')
    ax_curves.set_title('Training curves')
    ax_curves.legend()

  def save_checkpoint(self):
    checkpoint = {
        'epoch': self.epoch,
        'model_state_dict': self.model.state_dict(),
        'opt_state_dict': self.opt.state_dict(),
        'sched_state_dict': self.scheduler.state_dict(),
        'train_losses': self.train_losses,
        'test_crits': self.test_crits
        }
    print('  ... saving new model')
    torch.save(checkpoint, self.model_path)

  def load_from_path(self, path):
    print(' ... loading model from {}'.format(path))
    checkpoint = torch.load(path)
    self.epoch = checkpoint['epoch']
    self.model.load_state_dict(checkpoint['model_state_dict'])
    self.opt.load_state_dict(checkpoint['opt_state_dict'])
    self.scheduler.load_state_dict(checkpoint['sched_state_dict'])
    self.train_losses = checkpoint['train_losses']
    self.test_crits = checkpoint['test_crits']
    self.best_crit = min(self.test_crits)

class ANN(nn.Module):
    def __init__(self, input_size, output_size, mu, sig):
        super(ANN, self).__init__()
        self.fc1 = nn.Linear(input_size, 1000)
        self.fc3 = nn.Linear(1000, output_size)
        self.relu = nn.ReLU()
        self.register_buffer('mu_in', torch.tensor(mu[:input_size]))
        self.register_buffer('mu_out', torch.tensor(mu[input_size:output_size+input_size]))
        self.register_buffer('sig_in', torch.tensor(sig[:input_size]))
        self.register_buffer('sig_out', torch.tensor(sig[input_size:output_size+input_size]))

    def scale_in(self, x):
        return (x - self.mu_in.to(x.device)) / self.sig_in.to(x.device)
    
    def scale_out(self, y):
        return y * self.sig_out.to(y.device) + self.mu_out.to(y.device)

    def forward(self, x):
        x = self.scale_in(x)
        x = self.relu(self.fc1(x))
        x = self.fc3(x)
        x = self.scale_out(x)
        return x


def train(model, loader, loss_fn, optimizer, scheduler, device):
    model.train()
    running_loss = 0.0
    for i, (inputs, targets) in enumerate(loader):
        inputs, targets = inputs.to(device), targets.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = loss_fn(outputs, targets)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
    
    return running_loss / len(loader)
    

def test(model, test_loader, criterion, device):
    model.eval()
    total_loss = 0.0
    total_err = 0.0
    with torch.no_grad():
        for inputs, targets in test_loader:
            inputs, targets = inputs.to(device), targets.to(device)
            outputs = model(inputs)
            total_err += torch.norm(outputs - targets) / torch.norm(targets)
            loss = criterion(outputs, targets)
            total_loss += loss.item()
    print(f'Average test error: {100 * total_err / len(test_loader):2.4f}%')
    return total_loss / len(test_loader)

def main():
    # If no arguments are provided, inject defaults
    import sys
    if len(sys.argv) == 1:
        sys.argv.extend(["s.coords","10","25"])
    
    parser = argparse.ArgumentParser(description='Train ANN using PyTorch')
    parser.add_argument('data_file', type=str, help='Path to data file')
    parser.add_argument('input_size', type=int, help='Input size of the model')
    parser.add_argument('output_size', type=int, help='Output size of the model')
    parser.add_argument('--skip_columns', type=int, default=0, help='Number of columns in the specified data_file to skip. Default is 0 based on AERO-F output.')
    parser.add_argument('--skip_rows', type=int, default=0, help='Number of rows in the specified data_file to skip. Default is 0 based on AERO-F output.')
    args = parser.parse_args()

    # Load data
    data = np.loadtxt(args.data_file, skiprows=args.skip_rows, delimiter=',')
    #data = data[args.skip_rows:, :]  # <-- Original comment: do not remove
    data = data[:, args.skip_columns:]
    mu = np.mean(data, axis=0)
    std = np.std(data, axis=0)
    np.random.shuffle(data)
    inputs = data[:, :args.input_size]
    targets = data[:, args.input_size:]

    # Split data into train and test sets
    split_idx = int(TRAINING_FRAC * len(data))
    train_inputs, test_inputs = inputs[:split_idx], inputs[split_idx:]
    train_targets, test_targets = targets[:split_idx], targets[split_idx:]

    # Convert data to double precision
    train_inputs, train_targets = train_inputs.astype(np.float64), train_targets.astype(np.float64)
    test_inputs, test_targets = test_inputs.astype(np.float64), test_targets.astype(np.float64)

    # Create DataLoader
    train_dataset = TensorDataset(torch.DoubleTensor(train_inputs), torch.DoubleTensor(train_targets))
    test_dataset = TensorDataset(torch.DoubleTensor(test_inputs), torch.DoubleTensor(test_targets))
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE)

    # Initialize model, criterion, optimizer, scheduler, and device
    device = torch.device('cpu')
    model = ANN(args.input_size, args.output_size, mu, std).to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=LR_INIT,  weight_decay = 1e-10)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, threshold=1e-3, factor=0.1, patience=LR_PATIENCE, verbose=True)

    # Tensorboard writer
    writer = SummaryWriter()
    
    monitor = TrainingMonitor(MODEL_PATH, COMPLETION_PATIENCE, model, optimizer, scheduler)

    # ---- Measure training time ----
    start_time = time.time()

    # Training loop
    for epoch in range(EPOCHS):
        train_loss = train(model, train_loader, criterion, optimizer, scheduler, device)
        writer.add_scalar('training_loss', train_loss, epoch)
        test_loss = test(model, test_loader, criterion, device)
        scheduler.step(test_loss)
        writer.add_scalar('test_loss', test_loss, epoch)
        print(f'Epoch [{epoch+1}/{EPOCHS}], Test Loss: {test_loss:.4f}')
        if monitor.check_for_completion(train_loss, test_loss):
            break

    end_time = time.time()
    total_time = end_time - start_time
    print(f'Training complete! Total training time: {total_time:.2f} seconds')

    # Save model
    traced_model = torch.jit.trace(model, torch.rand(1, args.input_size).to(device))
    traced_model.save('traced_model.pt')

if __name__ == '__main__':
    main()
