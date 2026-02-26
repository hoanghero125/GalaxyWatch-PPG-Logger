from fastapi import FastAPI, WebSocket, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import obsws_python as obs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load config from config.yaml next to this script
_config_path = Path(__file__).parent / "config.yaml"
with open(_config_path, "r") as f:
    _raw_cfg = yaml.safe_load(f)


class Config:
    SERVER_HOST = _raw_cfg["server"]["host"]
    SERVER_PORT = _raw_cfg["server"]["port"]

    OBS_HOST = _raw_cfg["obs"]["host"]
    OBS_PORT = _raw_cfg["obs"]["port"]
    OBS_PASSWORD = _raw_cfg["obs"]["password"]

    _base_dir = Path(__file__).parent
    DATASET_ROOT = (_base_dir / _raw_cfg["paths"]["dataset_root"]).resolve()
    VIDEO_OUTPUT_PATH = (_base_dir / _raw_cfg["paths"]["video_output"]).resolve()

    DATASET_ROOT.mkdir(parents=True, exist_ok=True)
    VIDEO_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="PPG Data Collection Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SessionManager:
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.obs_client: Optional[obs.ReqClient] = None
        self.connected_clients: set = set()

    async def connect_obs(self):
        try:
            self.obs_client = obs.ReqClient(
                host=Config.OBS_HOST,
                port=Config.OBS_PORT,
                password=Config.OBS_PASSWORD
            )
            logger.info("Connected to OBS WebSocket")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to OBS: {e}")
            return False

    def create_session(self, subject_id: str, session_type: str) -> Dict[str, Any]:
        """Create new recording session"""
        timestamp = int(datetime.now().timestamp() * 1000)
        session_id = f"{subject_id}_{session_type}_{timestamp}"

        session_folder = Config.DATASET_ROOT / subject_id / f"{session_type}_{timestamp}"
        session_folder.mkdir(parents=True, exist_ok=True)

        video_filename = f"{subject_id}_{session_type}_{timestamp}.mp4"
        video_path = Config.VIDEO_OUTPUT_PATH / video_filename

        session = {
            "session_id": session_id,
            "subject_id": subject_id,
            "session_type": session_type,
            "start_timestamp": timestamp,
            "end_timestamp": None,
            "session_folder": str(session_folder),
            "video_filename": video_filename,
            "video_path": str(video_path),
            "sync_markers": {
                "watch_start": None,
                "watch_stop": None,
                "phone_start": None,
                "phone_stop": None,
                "video_start": None,
                "video_stop": None
            }
        }

        self.active_sessions[session_id] = session

        self._save_metadata(session)

        return session

    def _save_metadata(self, session: Dict[str, Any]):
        """Save session metadata"""
        metadata_path = Path(session["session_folder"]) / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(session, f, indent=2)

    async def start_recording(self, session_id: str) -> bool:
        """Start OBS recording"""
        if not self.obs_client:
            await self.connect_obs()

        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return False

            try:
                record_directory = str(Config.VIDEO_OUTPUT_PATH)
                self.obs_client.set_record_directory(record_directory)

                logger.info(f"OBS output directory set to: {record_directory}")
                logger.info(f"Video will be saved as: {session['video_filename']}")

            except Exception as config_err:
                logger.warning(f"Could not set OBS path (continuing anyway): {config_err}")

            self.obs_client.start_record()

            video_start_time = int(datetime.now().timestamp() * 1000)
            session["sync_markers"]["video_start"] = video_start_time

            self._save_metadata(session)

            logger.info(f"Started OBS recording for session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to start OBS recording: {e}")
            return False

    async def stop_recording(self, session_id: str) -> bool:
        """Stop OBS recording"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return False

            try:
                status = self.obs_client.get_record_status()
                if status.output_active:
                    self.obs_client.stop_record()
                    logger.info(f"Stopped OBS recording for session {session_id}")

                    await asyncio.sleep(2)

                    try:
                        video_dir = Config.VIDEO_OUTPUT_PATH
                        video_files = []

                        for ext in ['*.mp4', '*.mkv', '*.flv', '*.mov']:
                            video_files.extend(video_dir.glob(ext))

                        if video_files:
                            newest_file = max(video_files, key=lambda p: p.stat().st_mtime)

                            desired_filename = session['video_filename']
                            desired_path = video_dir / desired_filename

                            if newest_file != desired_path:
                                newest_file.rename(desired_path)
                                logger.info(f"Renamed video: {newest_file.name} -> {desired_filename}")
                                session['video_path'] = str(desired_path)
                            else:
                                logger.info(f"Video already has correct name: {desired_filename}")

                            self._save_metadata(session)
                        else:
                            logger.warning("No video files found to rename")

                    except Exception as rename_err:
                        logger.error(f"Failed to rename video: {rename_err}")
                else:
                    logger.warning(f"OBS was not recording for session {session_id}")
            except Exception as obs_error:
                logger.error(f"OBS stop error: {obs_error}")

            video_stop_time = int(datetime.now().timestamp() * 1000)
            session["sync_markers"]["video_stop"] = video_stop_time
            session["end_timestamp"] = video_stop_time

            self._save_metadata(session)

            return True

        except Exception as e:
            logger.error(f"Failed to stop session: {e}")
            return False

    def update_sync_marker(self, session_id: str, marker_name: str, timestamp: int):
        """Update sync marker"""
        session = self.active_sessions.get(session_id)
        if session:
            session["sync_markers"][marker_name] = timestamp
            self._save_metadata(session)

    async def save_sync_markers(self, session_id: str):
        """Save sync markers to CSV"""
        session = self.active_sessions.get(session_id)
        if not session:
            return False

        sync_csv_path = Path(session["session_folder"]) / "sync_markers.csv"

        with open(sync_csv_path, 'w') as f:
            f.write("event_type,timestamp,video_filename\n")
            markers = session["sync_markers"]
            for key, value in markers.items():
                if value:
                    f.write(f"{key},{value},{session['video_filename']}\n")

        logger.info(f"Saved sync markers for session {session_id}")
        return True

session_manager = SessionManager()

# ============== API Endpoints ==============

@app.on_event("startup")
async def startup_event():
    """Initialize OBS connection on startup"""
    await session_manager.connect_obs()

@app.get("/")
async def root():
    return {"status": "PPG Data Collection Server Running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    obs_connected = session_manager.obs_client is not None
    return {
        "status": "ok",
        "obs_connected": obs_connected,
        "active_sessions": len(session_manager.active_sessions)
    }

@app.post("/api/session/create")
async def create_session(subject_id: str = Form(...), session_type: str = Form(...)):
    """Create new recording session"""
    try:
        session = session_manager.create_session(subject_id, session_type)

        await broadcast_message({
            "type": "session_created",
            "session": session
        })

        return JSONResponse({
            "success": True,
            "session": session
        })
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/session/{session_id}/start")
async def start_session(session_id: str, phone_timestamp: int = Form(...)):
    """Start recording session"""
    try:
        session_manager.update_sync_marker(session_id, "phone_start", phone_timestamp)

        success = await session_manager.start_recording(session_id)

        if success:
            await broadcast_message({
                "type": "recording_started",
                "session_id": session_id
            })

            return JSONResponse({
                "success": True,
                "message": "Recording started"
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to start recording")

    except Exception as e:
        logger.error(f"Error starting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/session/{session_id}/stop")
async def stop_session(session_id: str, phone_timestamp: int = Form(...)):
    """Stop recording session"""
    try:
        session_manager.update_sync_marker(session_id, "phone_stop", phone_timestamp)

        success = await session_manager.stop_recording(session_id)

        if success:
            await session_manager.save_sync_markers(session_id)

            await broadcast_message({
                "type": "recording_stopped",
                "session_id": session_id
            })

            return JSONResponse({
                "success": True,
                "message": "Recording stopped"
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to stop recording")

    except Exception as e:
        logger.error(f"Error stopping session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/session/{session_id}/sync-marker")
async def update_sync_marker(
    session_id: str,
    marker_name: str = Form(...),
    timestamp: int = Form(...)
):
    """Update sync marker"""
    try:
        session_manager.update_sync_marker(session_id, marker_name, timestamp)
        return JSONResponse({
            "success": True,
            "message": f"Updated {marker_name}"
        })
    except Exception as e:
        logger.error(f"Error updating sync marker: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/session/{session_id}/upload/{file_type}")
async def upload_file(
    session_id: str,
    file_type: str,
    file: UploadFile = File(...)
):
    """Upload data file from smartphone"""
    try:
        session = session_manager.active_sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        file_path = Path(session["session_folder"]) / f"{file_type}.csv"

        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)

        logger.info(f"Uploaded {file_type}.csv for session {session_id}")

        return JSONResponse({
            "success": True,
            "message": f"Uploaded {file_type}.csv"
        })

    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions")
async def list_sessions():
    """List all sessions"""
    return JSONResponse({
        "sessions": list(session_manager.active_sessions.values())
    })

# ============== WebSocket for real-time communication ==============

async def broadcast_message(message: dict):
    """Broadcast message to all connected clients"""
    if session_manager.connected_clients:
        message_str = json.dumps(message)
        await asyncio.gather(
            *[client.send_text(message_str) for client in session_manager.connected_clients],
            return_exceptions=True
        )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    session_manager.connected_clients.add(websocket)
    logger.info("New WebSocket client connected")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            logger.info(f"Received WebSocket message: {message}")

            await websocket.send_json({
                "type": "ack",
                "message": "Received"
            })

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        session_manager.connected_clients.discard(websocket)
        logger.info("WebSocket client disconnected")

if __name__ == "__main__":
    print("=" * 60)
    print("PPG Data Collection Server")
    print("=" * 60)
    print(f"Dataset Root: {Config.DATASET_ROOT}")
    print(f"Video Output: {Config.VIDEO_OUTPUT_PATH}")
    print(f"OBS Connection: {Config.OBS_HOST}:{Config.OBS_PORT}")
    print("=" * 60)
    print(f"\nStarting server on http://{Config.SERVER_HOST}:{Config.SERVER_PORT}")
    print(f"API Docs available at http://localhost:{Config.SERVER_PORT}/docs")
    print("\n")

    uvicorn.run(app, host=Config.SERVER_HOST, port=Config.SERVER_PORT, log_level="info")
