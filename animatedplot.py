import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("csv_path", nargs="?", help="path to a recording, e.g. recordings/relaxed.csv")

CSV_PATH = parser.parse_args().csv_path or input("CSV path (e.g. recordings/relaxed.csv): ").strip().strip("\"'")
HAS_HEADER = True                           # set to False if the first row is already data
TIMESTAMP_UNIT = 1.0                        # seconds per timestamp tick: 1.0 = seconds, 1e-3 = milliseconds, 1e-6 = microseconds
                                            # (ignored if the timestamps are date/time strings)

df = pd.read_csv(CSV_PATH, header=0 if HAS_HEADER else None)

# timestamp is the first column, the 8 channels are the next 8 columns
ts = df.iloc[:, 0]
signals = df.iloc[:, 1:9].to_numpy(dtype=float)      # shape => [num_samples, 8]

# convert timestamps to seconds since the first sample
if pd.api.types.is_numeric_dtype(ts):
    time = ts.to_numpy(dtype=float) * TIMESTAMP_UNIT
else:
    time = pd.to_datetime(ts).astype("int64").to_numpy() / 1e9    # datetime strings -> seconds
time = time - time[0]

# animated plot of the first 'Z' samples of each channel, one subplot per channel
# one y-range for ALL channels, so the subplots are directly comparable
Z = 2000
signals, time = signals[:Z], time[:Z]
ymin, ymax = np.percentile(signals, [0.5, 99.5])

WINDOW = 1.0                                # seconds of signal visible at a time
SPEED = 1.0                                 # 1.0 = real time, 2.0 = twice as fast, etc.
INTERVAL = 20                               # ms between frames
total = time[-1]                            # length of the recording in seconds
WINDOW = min(WINDOW, total)

# setting up all the axes... 8 subplots for emg data and another for displaying time
fig, axs = plt.subplots(9, 1, figsize=(8, 9), gridspec_kw={"height_ratios": [4] * 8 + [1.5]})
plt.setp(axs[:8], xticks=[], ylim=(ymin, ymax))         # signals: no x ticks, shared y-range
axs[8].set(xlim=(0, total), yticks=[], xlabel="Time (s)")   # timeline: whole recording, in real timestamps
playhead = axs[8].axvline(0, color="red")               # the | that slides across timeline

# first window of data, found by timestamp rather than by sample count
end0 = np.searchsorted(time, WINDOW, side="right")
lines = []
for i in range(8):
    # draw each line once with the first window. we update the data later... faster than redrawing the axes
    line, = axs[i].plot(time[:end0], signals[:end0, i])
    lines.append(line)
    axs[i].set_xlim(0, WINDOW)
    axs[i].set_ylabel(f"Ch {i+1}")

# the time of the newest visible sample for each frame, advancing in real time
dt = INTERVAL / 1000 * SPEED
frame_times = np.arange(WINDOW, total + dt, dt)

# runs once per frame
def update(frame):
    t_end = frame_times[frame]              # right edge of the visible window (seconds)
    t_start = t_end - WINDOW                # left edge
    i0 = np.searchsorted(time, t_start, side="left")
    i1 = np.searchsorted(time, t_end, side="right")
    for i in range(8):
        lines[i].set_data(time[i0:i1], signals[i0:i1, i])
        axs[i].set_xlim(t_start, t_end)     # x-axis scrolls with the window
    playhead.set_xdata([t_end, t_end])      # a vertical line needs two x values (same x)
    return lines + [playhead]

# repeat = False => makes it stop on the last frame instead of looping
anim = FuncAnimation(fig, update, frames=len(frame_times), interval=INTERVAL, repeat=False)
plt.show()
# anim.save(filename="emg_data_animated.mp4")
