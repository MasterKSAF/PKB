"""
Fix RAG Builder vector dimension: add VECTOR_DIMENSION=312 to supervisor config
"""
import subprocess
import sys

container = "pkb-neuro"
conf_path = "/etc/supervisor/conf.d/supervisord.conf"

# Check current config
r = subprocess.run(
    ["docker", "exec", container, "cat", conf_path],
    capture_output=True, text=True, timeout=15
)
conf = r.stdout

if "VECTOR_DIMENSION" in conf:
    print("VECTOR_DIMENSION already set in supervisor config")
else:
    # Add VECTOR_DIMENSION after EMBEDDING_DIM line in [program:rag-builder] section
    old_line = '    EMBEDDING_DIM="%(ENV_EMBEDDING_DIM)s"'
    new_line = old_line + ',\n    VECTOR_DIMENSION="312"'
    conf = conf.replace(old_line, new_line)

    # Write back
    with open("/tmp/supervisord.conf", "w") as f:
        pass  # use docker cp approach instead
    import tempfile, os
    tmp = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".conf")
    tmp.write(conf)
    tmp.close()
    
    # Copy to container
    subprocess.run(
        ["docker", "cp", tmp.name, f"{container}:{conf_path}"],
        capture_output=True, text=True, timeout=15
    )
    os.unlink(tmp.name)
    print("VECTOR_DIMENSION=312 added to supervisor config")

# Restart rag-builder
print("Restarting rag-builder...")
r = subprocess.run(
    ["docker", "exec", container, "supervisorctl", "restart", "rag-builder"],
    capture_output=True, text=True, timeout=30
)
print(r.stdout.strip())
if r.returncode != 0:
    print(f"STDERR: {r.stderr.strip()}", file=sys.stderr)
