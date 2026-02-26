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

## 3. Data Collection Workflow

A complete recording session involves the PC server, OBS, and the Galaxy Watch working together. The server API can be called via the interactive Swagger UI at `http://localhost:8000/docs`, `curl`, or any HTTP client.

### Step 1: Start the PC Side

1. Open **OBS Studio** and make sure your video source is configured (e.g. webcam)
2. Start the server:
   ```bash
   cd server
   python main.py
   ```
3. Verify everything is connected:
   ```bash
   curl http://localhost:8000/health
   ```
   You should see `"obs_connected": true`.

### Step 2: Create a Session

Create a session with a subject ID and session type (e.g. `baseline`, `exercise`, `rest`):

```bash
curl -X POST http://localhost:8000/api/session/create \
  -d "subject_id=S_001" \
  -d "session_type=baseline"
```

The response contains the `session_id` — save it for the next steps. Example: `S_001_baseline_1740000000000`

### Step 3: Start Recording

Start OBS video recording and record the start timestamp:

```bash
curl -X POST http://localhost:8000/api/session/S_001_baseline_1740000000000/start \
  -d "phone_timestamp=$(date +%s000)"
```

OBS will begin recording. The video start time is saved as a sync marker.

### Step 4: Collect PPG Data on the Watch

1. Open **Galaxy PPG Logger** on the watch
2. Tap **Play** to begin PPG data collection
3. The watch collects PPG signals (green, red, IR) and stores them locally

> Optionally, record the watch start time as a sync marker:
> ```bash
> curl -X POST http://localhost:8000/api/session/S_001_baseline_1740000000000/sync-marker \
>   -d "marker_name=watch_start" \
>   -d "timestamp=$(date +%s000)"
> ```

### Step 5: Stop Collection

1. Tap **Pause** on the watch to stop PPG collection
2. Stop the server session (this stops OBS recording and saves sync markers):
   ```bash
   curl -X POST http://localhost:8000/api/session/S_001_baseline_1740000000000/stop \
     -d "phone_timestamp=$(date +%s000)"
   ```

### Step 6: Extract PPG Data from the Watch

PPG data is stored in a Room database on the watch. Pull it via ADB and export to CSV:

```bash
# Pull the database from the watch
adb pull /data/data/kaist.iclab.galaxyppglogger/databases/RoomDB ./RoomDB

# Export to CSV using sqlite3
sqlite3 -header -csv ./RoomDB "SELECT * FROM ppg;" > ppg.csv
```

> If `adb pull` gives a permission error, use root access:
> ```bash
> adb root
> adb pull /data/data/kaist.iclab.galaxyppglogger/databases/RoomDB ./RoomDB
> ```
>
> Alternatively, if your watch doesn't have root, you can use the **backup method**:
> ```bash
> adb exec-out run-as kaist.iclab.galaxyppglogger cat databases/RoomDB > RoomDB
> ```

### Step 7: Upload Data to the Session

Upload the exported CSV to the server so it's stored alongside the video:

```bash
curl -X POST http://localhost:8000/api/session/S_001_baseline_1740000000000/upload/ppg \
  -F "file=@ppg.csv"
```

### Step 8: Clean Up

Flush collected data from the watch for the next session:
- Tap **Flush** on the watch app, or
- Reinstall the app to reset the database

### Final Output

After a complete session, `PPG_Dataset/` will contain:

```
PPG_Dataset/
├── videos/
│   └── S_001_baseline_1740000000000.mp4    # OBS video recording
└── S_001/
    └── baseline_1740000000000/
        ├── metadata.json                    # Session info + timestamps
        ├── sync_markers.csv                 # Sync points for alignment
        └── ppg.csv                          # PPG signal data
```

**PPG CSV columns:** `id, dataReceived, timestamp, green, greenStatus, red, redStatus, ir, irStatus`

| Column | Description |
|--------|-------------|
| `id` | Auto-incremented row ID |
| `dataReceived` | Unix timestamp (ms) when the app received the data |
| `timestamp` | Sensor timestamp (ms) from the Samsung Health SDK |
| `green` | Green LED PPG value |
| `greenStatus` | Green signal quality status |
| `red` | Red LED PPG value |
| `redStatus` | Red signal quality status |
| `ir` | Infrared LED PPG value |
| `irStatus` | IR signal quality status |

---

## License

This project is licensed under the [MIT License](LICENSE).
