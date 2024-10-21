import shutil


def move_image(source_path: str, destination_path: str):
    shutil.move(source_path, destination_path)
