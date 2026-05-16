from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
ARCHIVE_DIR = DATA_DIR / "archive"
DB_PATH = DATA_DIR / "app.db"

MFA_CHECKPOINT = str(BASE_DIR / "mfa_conformer_sv" / "epoch=17_cosine_eer=0.72.ckpt")
MFA_INFERENCE_SCRIPT = str(BASE_DIR / "mfa_conformer_sv" / "newinference.py")
RAWGAT_MODEL = str(BASE_DIR / "RawGAT-ST-antispoofing-main" / "epoch_42.pth")
RAWGAT_INFERENCE_SCRIPT = str(BASE_DIR / "RawGAT-ST-antispoofing-main" / "inference.py")
RAWGAT_CONFIG = str(BASE_DIR / "RawGAT-ST-antispoofing-main" / "model_config_RawGAT_ST.yaml")
RISK_PROFILE_PATH = BASE_DIR / "app" / "configs" / "risk_profile.json"

API_HOST = "0.0.0.0"
API_PORT = 8000

# Maintenance strategy
UPLOAD_RETENTION_DAYS = 7
DB_RECORD_RETENTION_DAYS = 30
MAINTENANCE_INTERVAL_SECONDS = 3600
DB_ARCHIVE_PAGE_SIZE = 500
