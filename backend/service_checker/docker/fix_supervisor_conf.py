"""
Fix supervisor config for rag-builder: set EMBEDDING_DIM=312, VECTOR_DIMENSION=312
"""
import subprocess
import tempfile
import os

container = "pkb-neuro"

r = subprocess.run(
    ["docker", "exec", container, "cat", "/etc/supervisor/conf.d/supervisord.conf"],
    capture_output=True, text=True, timeout=15
)
conf = r.stdout

old_env = (
    '    EMBEDDING_PROVIDER="tei",\n'
    '    EMBEDDING_BASE_URL="%(ENV_EMBEDDING_BASE_URL)s",\n'
    '    EMBEDDING_API_URL="%(ENV_EMBEDDING_BASE_URL)s",\n'
    '    EMBEDDING_MODEL="%(ENV_EMBEDDING_MODEL)s",\n'
    '    EMBEDDING_DIM="%(ENV_EMBEDDING_DIM)s",\n'
    '    VECTOR_DIMENSION="%(ENV_EMBEDDING_DIM)s",\n'
    '    EMBEDDING_DIM="%(ENV_EMBEDDING_DIM)s",'
)

new_env = (
    '    EMBEDDING_PROVIDER="tei",\n'
    '    EMBEDDING_BASE_URL="%(ENV_EMBEDDING_BASE_URL)s",\n'
    '    EMBEDDING_API_URL="%(ENV_EMBEDDING_BASE_URL)s",\n'
    '    EMBEDDING_MODEL="%(ENV_EMBEDDING_MODEL)s",\n'
    '    EMBEDDING_DIM="312",\n'
    '    VECTOR_DIMENSION="312",'
)

conf = conf.replace(old_env, new_env)

tmp = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".conf")
tmp.write(conf)
tmp.close()

subprocess.run(
    ["docker", "cp", tmp.name, f"{container}:/etc/supervisor/conf.d/supervisord.conf"],
    capture_output=True, text=True, timeout=15
)
os.unlink(tmp.name)
print("Config fixed with EMBEDDING_DIM=312, VECTOR_DIMENSION=312")

# Verify
r = subprocess.run(
    ["docker", "exec", container, "grep", "-A3", "EMBEDDING_DIM",
     "/etc/supervisor/conf.d/supervisord.conf"],
    capture_output=True, text=True, timeout=15
)
print(r.stdout)
