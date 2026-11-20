# theawesomeproject
pretty awesome project

detecting emg signals in the hand and fingers...

# EMG Recorder

Live-plots all 8 channels of a Myo armband and records them to CSV with the press of a key.

## What you need

**Hardware**
- Myo armband (charged)
- The Myo's Bluetooth USB dongle (plugged in directly, not through a flaky hub)

**Software**
- Python 3.8+
- A desktop environment where Matplotlib can open a window (Tk or Qt backend)

**Python packages**

```bash
pip install numpy pandas matplotlib pyomyo
```

`pyomyo` pulls in `pyserial` for talking to the dongle. `pandas` is only needed for the plotting scripts. Everything else used in the scripts (`csv`, `multiprocessing`, `argparse`, etc.) is in the standard library.

Optional: [ffmpeg](https://ffmpeg.org/) if you want to save the animated plot as an MP4.

## Before you run it

1. Plug in the Myo dongle.
2. Make sure **Myo Connect (Thalmic's official software) is closed**. It grabs the dongle and will block pyomyo.
3. Put the armband on and make sure it's awake (give it a wiggle).

## Usage

```bash
python record_emg.py
```

A window opens with 8 live EMG plots. The script prints the battery level, the Myo's LEDs turn green, and it vibrates once when connected.

1. **(Optional) Name the file:** click the "File name" box, type a name, and press **Enter**. Leave it blank to get an automatic timestamped name.
2. Press **SPACE** to start recording. The title turns red and shows a running timer.
3. Press **SPACE** again to stop. The recording is saved and the title turns green with the file name.
4. Repeat as many times as you like. Each recording is saved separately.

Notes:
- SPACE is ignored while the cursor is active in the file name box. Press Enter first.
- The name is locked in when you press SPACE to start, so change it before recording.
- Closing the window mid-recording saves what you have so far.
- Ctrl+C in the terminal also shuts things down.

## Output

Files go in a `recordings/` folder (created automatically) next to the script.

| Column | Meaning |
|---|---|
| `timestamp` | Seconds since the first recorded sample (starts at 0) |
| `ch1` ... `ch8` | Preprocessed EMG value for each of the 8 sensors |

- Names are cleaned up (spaces become underscores, unsafe characters removed) and `.csv` is added if missing.
- Existing files are never overwritten. A repeated name gets `_1`, `_2`, etc. appended.
- Every sample received is recorded, even if the plot can't keep up. Timestamps are taken as each sample arrives.
- An empty recording is not saved.

## Viewing a recording

Both plotting scripts take the path to a recorded CSV, either as an argument or by prompting you for it.

### Basic plot (`basicplot.py`)

A static plot with one subplot per channel (8 total), sharing an x-axis.

```bash
python basicplot.py recordings/relaxed.csv
```

- Plots the first 1000 samples of each channel. Change `Z` in the script to show more or fewer.
- The x-axis is the sample number, not time.
- If you leave off the path, the script asks for it.

### Animated plot (`animatedplot.py`)

A scrolling playback of the recording, like a replay of the live view.

```bash
python animatedplot.py recordings/relaxed.csv
```

- 8 channel subplots plus a timeline at the bottom with a red playhead showing where you are in the recording.
- All channels share one y-range (0.5th to 99.5th percentile of the data), so they're directly comparable.
- Plays in real time and stops on the last frame.
- Uses the first 2000 samples (`Z` in the script).

Settings at the top of the script:

| Setting | What it does |
|---|---|
| `HAS_HEADER` | Set to `False` if the first CSV row is data, not column names (recordings from `record_emg.py` have a header) |
| `TIMESTAMP_UNIT` | Seconds per timestamp tick (`1.0` for seconds, `1e-3` for ms). Ignored for date/time strings. Leave at `1.0` for recordings from `record_emg.py` |
| `Z` | How many samples to load |
| `WINDOW` | Seconds of signal visible at once |
| `SPEED` | Playback speed (`2.0` = twice as fast) |
| `INTERVAL` | Milliseconds between frames |

To save the animation, uncomment the `anim.save(...)` line at the bottom (needs ffmpeg).

Both scripts expect the CSV layout from the recorder: timestamp in the first column, then 8 channel columns.

## Troubleshooting

- **No window / backend error:** the script prints the Matplotlib backend on startup. If it's a non-interactive one (e.g. `agg`), install Tk (`python3-tk` on Linux) or `PyQt5`, or set `MPLBACKEND=TkAgg`.
- **Can't find or connect to the Myo:** check the dongle is plugged in, Myo Connect is closed, and the armband is charged and awake. Unplug and replug the dongle, then retry.
- **Linux permissions on the dongle:** you may need to add your user to the `dialout` group or add a udev rule.
- **Flat or noisy plots:** make sure the armband is snug against bare skin on the forearm and the LEDs are lit.
