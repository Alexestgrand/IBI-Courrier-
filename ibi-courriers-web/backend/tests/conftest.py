import os
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ENVIRONMENT", "development")
_tmp = tempfile.gettempdir()
os.environ.setdefault("UPLOAD_DIR", os.path.join(_tmp, "ibi-test-uploads"))
os.environ.setdefault("BACKUP_DIR", os.path.join(_tmp, "ibi-test-backups"))
os.environ.setdefault("MIGRATION_DIR", os.path.join(_tmp, "ibi-test-migration"))
