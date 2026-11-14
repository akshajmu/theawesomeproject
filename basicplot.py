import numpy as np
import matplotlib.pyplot as plt

# load the file with np.load. each key is an array.
data = np.load('datasets/myo_ds_30l_10ol.npz')
#print(data.files)                      # shows the array names inside the file

# get the arrays from the npz file. 'X' is emg data, 'y' is the labels
emg = data['X']                         # shape => [N, 30, 8]
labels = data['y']                      # length of N
# print(emg.shape, labels.shape)

# consecutive windows overlap by 10 readings, so each window starts 20 reading after the previous one.
# keep only the first 20 readings of each window, and the other 10 are repeated at the start of the next window.
# stitch them all together into one long signal [N*20, 8]
signal = emg[:, :20, :].reshape(-1, 8)

# plot the first 'Z' signals of each channel, one subplot per channel
Z = 1000
fig, axs = plt.subplots(8, 1, sharex=True)
for i in range(8):
    axs[i].plot(signal[:Z, i])
 
plt.show()
