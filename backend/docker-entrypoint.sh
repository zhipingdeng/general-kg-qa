#!/bin/sh
set -e

echo "==> Creating MySQL tables..."
python -c "
from app.config import get_settings
from app.database.mysql import get_engine, Base
from app.models.user import User
s = get_settings()
engine = get_engine(host=s.mysql_host, port=s.mysql_port, user=s.mysql_user, password=s.mysql_password, database=s.mysql_database)
Base.metadata.create_all(bind=engine)
print('  Tables created.')
"

# Build Milvus + BM25 index if collection is empty or doesn't exist
echo "==> Checking Milvus index..."
python -c "
import sys
sys.path.insert(0, '.')
from app.database.milvus_client import MilvusClient
from app.config import get_settings
s = get_settings()
m = MilvusClient(host=s.milvus_host, port=s.milvus_port)
if not m.has_collection(s.milvus_collection):
    print('  Collection not found, building index...')
    import subprocess
    subprocess.run([sys.executable, 'scripts/build_index.py'], check=True)
elif m.count(s.milvus_collection) == 0:
    print('  Collection empty, building index...')
    import subprocess
    subprocess.run([sys.executable, 'scripts/build_index.py'], check=True)
else:
    print(f'  Index OK: {m.count(s.milvus_collection)} documents')
"

echo "==> Starting server..."
exec "$@"
