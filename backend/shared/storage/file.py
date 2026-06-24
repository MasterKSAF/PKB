import os
import mimetypes
from pathlib import Path
from typing import List, Dict, Any

#
#  operations with file 
#  

def save_file(file_data: bytes, filename: str, path: str = "files") -> str:
    """Saves file data to the specified directory and returns the full path. Raises FileExistsError if it already exists."""
    target_dir = Path(path)
    if not target_dir.exists() or not target_dir.is_dir():
        raise NotADirectoryError(f"Directory not found: {path}")
    
    file_path = target_dir / filename
    if file_path.exists():
        raise FileExistsError(f"File {filename} already exists in {path}")
        
    with open(file_path, "wb") as f:
        f.write(file_data)
        
    return str(file_path)

def get_file(filename: str, path: str = "files") -> bytes:
    """Reads and returns the content of the file."""
    file_path = Path(path) / filename
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"File {filename} not found in {path}")
        
    with open(file_path, "rb") as f:
        return f.read()

def delete_file(filename: str, path: str = "files") -> bool:
    """Deletes the specified file. Raises FileNotFoundError if the file does not exist."""
    file_path = Path(path) / filename
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"File {filename} not found in {path}")
        
    os.remove(file_path)
    return True

def get_file_info(filename: str, path: str = "files") -> Dict[str, Any]:
    """Returns basic file information including size and mime type."""
    file_path = Path(path) / filename
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"File {filename} not found in {path}")
        
    return {
        "filename": filename,
        "path": str(file_path),
        "size": get_file_size(filename, path),
        "mime_type": get_file_mime_type(filename, path),
        "metadata": get_file_metadata(filename, path)
    }

def get_file_list(path: str = "files") -> List[str]:
    """Returns a list of filenames in the specified directory."""
    target_dir = Path(path)
    if not target_dir.exists() or not target_dir.is_dir():
        raise NotADirectoryError(f"Directory not found: {path}")
    
    return [f.name for f in target_dir.iterdir() if f.is_file()]

def get_file_size(filename: str, path: str = "files") -> int:
    """Returns the size of the file in bytes."""
    file_path = Path(path) / filename
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"File {filename} not found in {path}")
        
    return os.path.getsize(file_path)

def get_file_mime_type(filename: str, path: str = "files") -> str:
    """Guesses and returns the MIME type of the file based on its extension."""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"

def get_file_metadata(filename: str, path: str = "files") -> Dict[str, float]:
    """Returns OS-level metadata for the file (creation and modification times)."""
    file_path = Path(path) / filename
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"File {filename} not found in {path}")
        
    stat_info = os.stat(file_path)
    return {
        "created_at": stat_info.st_ctime,
        "modified_at": stat_info.st_mtime
    }
