import pandas as pd
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser()
parser.add_argument("csv_path", nargs="?", help="path to a recording, e.g. recordings/relaxed.csv")

CSV_PATH = parser.parse_args().csv_path or input("CSV path (e.g. recordings/relaxed.csv): ").strip().strip("\"'")
HAS_HEADER = True                           # set to False if the first row is already data

df = pd.read_csv(CSV_PATH, header=0 if HAS_HEADER else None)

# timestamp is the first column, the 8 channels are the next 8 columns
timestamps = df.iloc[:, 0].to_numpy()
signal = df.iloc[:, 1:9].to_numpy(dtype=float)      # shape => [num_samples, 8]

# plot the first 'Z' samples of each channel, one subplot per channel
Z = 1000
fig, axs = plt.subplots(8, 1, sharex=True)
for i in range(8):
    axs[i].plot(signal[:Z, i])

plt.show()
