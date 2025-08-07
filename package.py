from pathlib import Path
import re
import shutil

# Create Package of this project using the version number set in the __init__.py file.

ADD_ON_NAME = "spa_sequencer"


def main():
    parent_dir = Path(__file__).parent
    addon_dir = parent_dir.joinpath("spa_sequencer")
    dist_dir = parent_dir / "dist"
    output_dir = dist_dir / "output"
    staging_dir = output_dir / ADD_ON_NAME
    init_file = addon_dir / "__init__.py"

    # Ensure Output/Staging Directories exist
    staging_dir.mkdir(parents=True, exist_ok=True)

    # Clear all file/folders in output Directory
    clear_directory(output_dir)

    # Copy Files to Staging Directory
    copy_directory_contents(addon_dir, staging_dir)

    version = get_version_number(init_file)
    shutil.make_archive(
        dist_dir.joinpath(f"{ADD_ON_NAME}_{version}"), 'zip', output_dir
    )


def clear_directory(directory: Path):
    if not directory.exists():
        return
    for child in directory.rglob("*"):
        if child.is_file():
            child.unlink()
            print("Removing", child.name)
        else:
            shutil.rmtree(child)


def copy_directory_contents(source_dir: Path, target_dir: Path):
    for file_path in source_dir.glob('*.py'):
        dst_path = target_dir / file_path.name
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(file_path, dst_path)

    for dir_path in source_dir.glob("*"):
        if not dir_path.is_dir():
            continue
        dst_path = target_dir / dir_path.name
        shutil.copytree(dir_path, dst_path)
    for dir_path in target_dir.rglob("*"):
        if dir_path.name == "__pycache__":
            shutil.rmtree(dir_path)
    # Remove __pycache__ directories
    for dir_path in target_dir.rglob("*"):
        if dir_path.name == "__pycache__":
            shutil.rmtree(dir_path)

    # Copy blender_manifest.toml
    manifest_file = source_dir / "blender_manifest.toml"
    shutil.copy(manifest_file, target_dir / "blender_manifest.toml")


def get_version_number(file: Path) -> str:
    """
    Extracts the add-on version number from blender_manifest.toml, ignoring schema_version.
    Expects a line like: version = "1.2.3"
    Returns the version as "1_2_3"
    """
    manifest_file = file.parent / "blender_manifest.toml"
    if not manifest_file.exists():
        raise FileNotFoundError(f"{manifest_file} does not exist")

    with open(manifest_file, 'r') as f:
        for line in f:
            # Only match lines that start with 'version' (not 'schema_version')
            if re.match(r'^\s*version\s*=', line):
                pattern = r'version\s*=\s*"(\d+)\.(\d+)\.(\d+)"'
                matches = re.search(pattern, line)
                if matches and len(matches.groups()) == 3:
                    return f"{matches.group(1)}_{matches.group(2)}_{matches.group(3)}"
    raise ValueError(f"Could not find version number in {manifest_file}")


if __name__ == "__main__":
    main()
