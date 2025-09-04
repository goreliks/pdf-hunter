import hashlib
import pathlib
from typing import Dict, Union

def calculate_file_hashes(file_path: Union[str, pathlib.Path], chunk_size: int = 8192) -> Dict[str, str]:
    """
    Calculates SHA1 and MD5 hashes for a file efficiently.

    Args:
        file_path: Path to the file to hash.
        chunk_size: Size of chunks to read at a time (in bytes).

    Returns:
        A dictionary containing 'sha1' and 'md5' hash values.
        
    Raises:
        FileNotFoundError: If the specified file does not exist.
        IsADirectoryError: If the path points to a directory.
    """
    file_path = pathlib.Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not file_path.is_file():
        raise IsADirectoryError(f"Path is not a file: {file_path}")
    
    sha1_hash = hashlib.sha1()
    md5_hash = hashlib.md5()
    
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                sha1_hash.update(chunk)
                md5_hash.update(chunk)
    except OSError as e:
        raise OSError(f"Error reading file {file_path}: {e}")
    
    return {
        'sha1': sha1_hash.hexdigest(),
        'md5': md5_hash.hexdigest()
    }


if __name__ == "__main__":
    file_path = "/Users/gorelik/Courses/pdf-hunter/tests/87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13.pdf"
    print(calculate_file_hashes(file_path))