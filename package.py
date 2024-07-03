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


def get_version_number(file: Path) -> str:
    with open(file, 'r') as f:
        content = f.read()

    pattern = r".version.:+.\(([0-9]+), ([0-9]+), ([0-9])\)"
    matches = re.search(pattern, content)

    if not matches or len(matches.groups()) != 3:
        raise ValueError(f"Could not find version number in {file}")

    return f"{matches.group(1)}_{matches.group(2)}_{matches.group(3)}"


if __name__ == "__main__":
    main()
