import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# load the file with np.load. each key is an array.
data = np.load('datasets/myo_ds_30l_10ol.npz')
# print(data.files)

# get the arrays from the npz file. 'X' is emg data, 'y' is the labels
emg = data['X']                             # shape => [N, 30, 8]
labels = data['y']                          # length of N
# print(emg.shape, labels.shape)

# consecutive windows overlap by 10 readings, so each window starts 20 reading after the previous one.
# keep only the first 20 readings of each window, and the other 10 are repeated at the start of the next window.
# stitch them all together into one long signal [N*20, 8]
signals = emg[:, :20, :].reshape(-1, 8)

# animated plot of the first 'Z' signals of each channel, one subplot per channel
# one y-range for ALL channels, taken from the whole recording, so the subplots are directly comparable
Z = 2000
signals = signals[:Z]
ymin, ymax = np.percentile(signals, [0.5, 99.5])

RATE, STEP, INTERVAL = 200, 4, 20           # samples/sec, samples per frame (4 = real time), ms per frame
WINDOW = RATE                               # shows 1 second at a time
time = np.arange(len(signals)) / RATE       # time in seconds for every sample

# setting up all the axes... 8 subplots for emg data and another for displaying time
fig, axs = plt.subplots(9, 1, figsize=(8, 9), gridspec_kw={"height_ratios": [4] * 8 + [1.5]})
plt.setp(axs[:8], xticks=[], ylim=(ymin, ymax))                             # signals: no x axis, shared y-range
axs[8].set(xlim=(0, len(signals) / RATE), yticks=[], xlabel="Time (s)")     # timeline: whole recording
playhead = axs[8].axvline(0, color="red")                                   # the | that slides across timeline

lines = []
for i in range(8):
    # draw each line once with placeholder data. we will change the ydata later... faster than redrawing the axes
    line, = axs[i].plot(time[:WINDOW], signals[:WINDOW, i])
    lines.append(line)
    axs[i].set_ylim(ymin, ymax)
    axs[i].set_ylabel(f"Ch {i+1}")

axs[-1].set_xlabel("Time (s)")

# runs once per frame
def update(frame):
    # where the visible window starts: it moves forward 'STEP' samples per frame
    start = frame * STEP
    for i in range(8):
        lines[i].set_ydata(signals[start:start + WINDOW, i])
    t = (start + WINDOW) / RATE             # time of the newest sample
    playhead.set_xdata([t, t])              # a vertical line needs two x values (same x)
    return lines + [playhead]

# start animation
# frames = how many frames fit before window hits end of data
# repeat = False => makes it stop on the last frame instead of looping

n_frames = (len(signals) - WINDOW) // STEP + 1
anim = FuncAnimation(fig, update, frames = n_frames, interval = INTERVAL, repeat = False)
plt.show()