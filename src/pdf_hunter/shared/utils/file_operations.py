import pathlib

def ensure_output_directory(directory_path: pathlib.Path):
    """
    Ensures that the specified directory exists, creating it if necessary.

    Args:
        directory_path: A pathlib.Path object for the directory.
    
    Raises:
        OSError: If the path exists but is not a directory.
    """
    if directory_path.exists() and not directory_path.is_dir():
        raise OSError(f"Path '{directory_path}' exists but is not a directory.")
    
    directory_path.mkdir(parents=True, exist_ok=True)