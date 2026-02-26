# GalaxyWatch PPG Logger

PPG signal collection from Samsung Galaxy Watch using the Health Sensor SDK, with a FastAPI server for session management and OBS video synchronization.

## Credits

This project is based on **GalaxyPPG-Logger** by KAIST ICLab. The original codebase supported multi-sensor collection (PPG, heart rate, accelerometer, skin temperature) with a companion smartphone app.

> **Park, S., Zheng, D. & Lee, U.** (2025).
> *A PPG Signal Dataset Collected in Semi-Naturalistic Settings Using Galaxy Watch*.
> *Scientific Data*, 12, 892. [https://doi.org/10.1038/s41597-025-05152-z](https://doi.org/10.1038/s41597-025-05152-z)

Original repository: [Kaist-ICLab/android-tracker](https://github.com/Kaist-ICLab/android-tracker)

---

## Project Structure

```
GalaxyWatch-PPG-Logger/
├── wearable/          # Galaxy Watch app (Kotlin / Wear OS)
├── server/            # PC data collection server (Python / FastAPI)
├── build-logic/       # Gradle convention plugins
├── gradle/            # Gradle version catalog
├── LICENSE
└── README.md
```

---

## 1. Wearable App (Galaxy Watch)

### Features

- **Play / Pause** button to start and stop PPG data collection
- **Flush** button to delete collected data from local storage
- PPG signals (green, red, IR) are stored locally in a Room database
- Runs as a foreground service with an ongoing activity notification

### Prerequisites

1. **Samsung Health Sensor SDK** — Download the AAR file and place it in `wearable/libs/`:
   - [Samsung Health Sensor SDK](https://developer.samsung.com/health/sensor/overview.html)

2. **Health Developer Mode** — On the watch, go to **Settings > Applications > Health Platform** and tap the top area multiple times to enable Dev mode. This bypasses the Samsung partner approval requirement.

3. **Wireless Debugging** — Set up ADB over Wi-Fi to deploy the app:
   - [Wireless Debugging Guide](https://developer.android.com/training/wearables/get-started/debugging)

### Build & Install

**Option A: From Android Studio**

1. Open the project in Android Studio
2. Ensure the Samsung Health Sensor SDK AAR is in `wearable/libs/`
3. Connect to your Galaxy Watch via wireless debugging
4. Run the `wearable` module

**Option B: Install via APK**

If you already have a built APK (or don't want to use Android Studio), you can sideload it directly.

1. Build the APK (if you haven't already):
   ```bash
   ./gradlew :wearable:assembleDebug
   ```
   The APK will be at `wearable/build/outputs/apk/debug/wearable-debug.apk`

2. Enable **Developer Options** on the watch:
   - Go to **Settings > About Watch > Software** and tap **Software Version** 5 times

3. Enable **ADB Debugging**:
   - Go to **Settings > Developer Options** and turn on **ADB Debugging**
   - For wireless: also enable **Debug over Wi-Fi** and note the IP address shown

4. Connect via ADB:
   ```bash
   adb connect <watch-ip>:<port>
   ```

5. Install the APK:
   ```bash
   adb install wearable/build/outputs/apk/debug/wearable-debug.apk
   ```

### Usage

1. Open **Galaxy PPG Logger** on the watch
2. Grant all requested permissions (body sensors, activity recognition, notifications)
3. Wait for the service to connect (spinner disappears)
4. Tap the **Play** button to start PPG collection
5. Tap **Pause** to stop collection
6. Tap **Flush** to delete all collected data from local storage

---

## 2. PC Server

A FastAPI server that manages recording sessions, controls OBS Studio for synchronized video capture, and receives uploaded data files.

### Features

- Create and manage recording sessions with subject ID and session type
- Start/stop OBS Studio recording via WebSocket
- Automatically rename video files to match session naming convention
- Upload sensor data CSV files from external sources
- Track sync markers (watch start/stop, phone start/stop, video start/stop)
- WebSocket endpoint for real-time status updates
- Interactive API docs at `/docs`

### Prerequisites

- Python 3.10+
- OBS Studio (v28+)

### OBS Studio Setup

The server controls OBS recording via WebSocket. OBS 28+ includes the obs-websocket plugin by default — you just need to enable it.

1. Install [OBS Studio](https://obsproject.com/download) if you haven't already
2. Open OBS and go to **Tools > WebSocket Server Settings**
3. Check **Enable WebSocket Server**
4. Set a **Server Password** (must match the `obs.password` in `config.yaml`)
5. Note the **Server Port** (default: `4455`)
6. Click **OK**
7. Set up your video source (e.g. webcam, screen capture) in OBS as you normally would
8. **Keep OBS running** before starting the server

> The server will attempt to connect to OBS on startup. If OBS is not running, the server still starts — but recording endpoints will fail until OBS is available. Check `GET /health` to verify OBS connection status.

### Setup

Using **conda**:

```bash
conda create -n ppg-server python=3.10 -y
conda activate ppg-server
cd server
pip install -r requirements.txt
```

Or using **venv**:

```bash
cd server
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Configuration

Edit `server/config.yaml`:

```yaml
server:
  host: "0.0.0.0"
  port: 8000

obs:
  host: "localhost"
  port: 4455
  password: "your_obs_password"

paths:
  dataset_root: "../PPG_Dataset"
  video_output: "../PPG_Dataset/videos"
```

Paths are relative to the `server/` directory. By default, `PPG_Dataset/` is created at the project root. You can also use absolute paths if needed.

### Run

```bash
cd server
python main.py
```

The server starts at `http://localhost:8000`. API documentation is available at `http://localhost:8000/docs`.

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check (OBS connection status) |
| `POST` | `/api/session/create` | Create a new recording session |
| `POST` | `/api/session/{id}/start` | Start OBS recording |
| `POST` | `/api/session/{id}/stop` | Stop OBS recording and save sync markers |
| `POST` | `/api/session/{id}/sync-marker` | Update a sync marker |
| `POST` | `/api/session/{id}/upload/{type}` | Upload a CSV data file |
| `GET` | `/api/sessions` | List all active sessions |
| `WS` | `/ws` | WebSocket for real-time updates |

### Output Structure

Each session creates the following:

```
PPG_Dataset/
├── videos/
│   └── S_001_baseline_1234567890.mp4
└── S_001/
    └── baseline_1234567890/
        ├── metadata.json
        ├── sync_markers.csv
        └── ppg.csv
```

---

## License

This project is licensed under the [MIT License](LICENSE).
