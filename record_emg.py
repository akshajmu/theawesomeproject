import csv
import multiprocessing
import os
import queue
import time
from datetime import datetime

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import animation
from matplotlib.widgets import TextBox
from pyomyo import Myo, emg_mode

QUEUE_SIZE = 100
SENSORS = 8
OUTPUT_DIR = "recordings"
READY_TEXT = "Press SPACE to record"

# Myo Set Up
def worker(q):
    m = Myo(mode=emg_mode.PREPROCESSED)
    m.connect()
    m.add_emg_handler(lambda emg, movement: q.put((time.time(), emg)))      # Timestamp each sample as it arrives so recorded time stays accurate without delays due to any other processes
    m.add_battery_handler(lambda bat: print("Battery level:", bat))
    m.set_leds([0, 255, 0], [0, 255, 0])
    m.vibrate(1)
    try:
        while True:
            m.run()
    except KeyboardInterrupt:
        pass
    finally:
        m.disconnect()

# File Set Up
def build_path(name):
    """Turn the typed name into a safe, non-clashing path inside OUTPUT_DIR."""
    name = name.strip().replace(" ", "_")
    name = "".join(c for c in name if c.isalnum() or c in "-_.").lstrip(".")
    if not name:
        name = f"emg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if not name.lower().endswith(".csv"):
        name += ".csv"
    path = os.path.join(OUTPUT_DIR, name)
    base, ext = os.path.splitext(path)
    n = 1
    while os.path.exists(path):  # never overwrite an earlier recording
        path = f"{base}_{n}{ext}"
        n += 1
    return path

# Writing to File
def save_recording(rows, name=""):
    """Write rows to CSV. Returns the saved file's name, or None if empty."""
    if not rows:
        print("Recording was empty, nothing saved.")
        return None
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = build_path(name)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp"] + [f"ch{i + 1}" for i in range(SENSORS)])
        t0 = rows[0][0]  # first sample becomes t = 0
        writer.writerows((r[0] - t0, *r[1:]) for r in rows)
    print(f"Saved {len(rows)} samples to {path}")
    return os.path.basename(path)


if __name__ == "__main__":
    print("Backend:", matplotlib.get_backend())
    print("Type a file name in the box (press Enter), then SPACE to start/stop recording.")

    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=worker, args=(q,), daemon=True)
    p.start()

    # Plot Set Up
    plt.rcParams["figure.figsize"] = (4, 8)
    fig, axes = plt.subplots(SENSORS, 1)
    fig.canvas.manager.set_window_title("8 Channel EMG plot")
    colors = matplotlib.colormaps["tab10"].colors

    buffer = np.zeros((QUEUE_SIZE, SENSORS))
    lines = []
    for i, ax in enumerate(axes):
        (line,) = ax.plot(range(QUEUE_SIZE), buffer[:, i], color=colors[i])
        ax.set_ylim(0, 1024)
        lines.append(line)

    status = fig.suptitle(READY_TEXT, color="gray", fontsize=10)
    # Leave room at the bottom for the file name box and at the top for the title
    fig.tight_layout(rect=[0, 0.07, 1, 0.95])

    # File name box
    box_ax = fig.add_axes([0.32, 0.015, 0.6, 0.04])
    name_box = TextBox(box_ax, "File name ", initial="")

    def typing():
        # True while the cursor is active inside the file name box
        return getattr(name_box, "capturekeystrokes", False)

    # Pressing Enter ends typing, so SPACE works again right away
    name_box.on_submit(lambda _text: name_box.stop_typing())

    # Recording state
    state = {"recording": False, "rows": [], "start": 0.0, "filename": ""}

    def toggle_recording():
        if not state["recording"]:
            state["rows"] = []
            state["filename"] = name_box.text  # name is locked in at start
            state["start"] = time.time()
            state["recording"] = True
            status.set_color("red")
            status.set_text("Recording 00:00.0")
            print("Recording started.")
        else:
            state["recording"] = False
            print("Recording stopped.")
            saved = save_recording(state["rows"], state["filename"])
            state["rows"] = []
            if saved:
                status.set_text(f"{saved} saved")
                status.set_color("green")
            else:
                status.set_text(READY_TEXT)
                status.set_color("gray")
        fig.canvas.draw_idle()

    def on_key(event):
        # Ignore space while typing in the file name box
        if event.key in (" ", "space") and not typing():
            toggle_recording()

    fig.canvas.mpl_connect("key_press_event", on_key)

    def animate(_):
        global buffer

        # Live timer
        if state["recording"]:
            mins, secs = divmod(time.time() - state["start"], 60)
            status.set_text(f"Recording {int(mins):02d}:{secs:04.1f}")

        new = []
        while True:
            try:
                new.append(q.get_nowait())
            except queue.Empty:
                break
        if not new:
            return lines

        # Record every sample received (not just the ones that get plotted)
        if state["recording"]:
            for ts, emg in new:
                state["rows"].append((ts, *emg))

        samples = np.array([emg for _, emg in new])[-QUEUE_SIZE:]
        buffer = np.vstack((buffer, samples))[-QUEUE_SIZE:]
        for i in range(SENSORS):
            lines[i].set_ydata(buffer[:, i])
            axes[i].set_ylim(0, max(1024, buffer[:, i].max()))
        return lines

    anim = animation.FuncAnimation(
        fig, animate, interval=20, blit=False, cache_frame_data=False
    )

    try:
        plt.show()
    finally:
        # If the window is closed mid-recording, don't lose the data
        if state["recording"]:
            print("Window closed while recording, saving.")
            save_recording(state["rows"], state["filename"])
        p.terminate()