import os

def find_project_root(current_path):
    while current_path != os.path.dirname(current_path):
        if os.path.exists(os.path.join(current_path, '.gitignore')):
            return current_path
        current_path = os.path.dirname(current_path)
    return current_path
