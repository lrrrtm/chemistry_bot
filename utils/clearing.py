import os
import shutil

from db.crud import get_pool_by_id


def clear_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            pass


def clear_trash_by_db(folder: str):
    counter = 0

    filenames = os.listdir(folder)
    filenames = [el for el in filenames if len(el.split('.')) == 2 and el.split('.')[0].isnumeric()]
    for file in filenames:
        question = get_pool_by_id(int(file.split('.')[0]))
        if question is None:
            try:
                print('removing', file)
                os.remove(os.path.join(folder, file))
                print('removed', file)
                counter += 1
            except Exception:
                pass

    return counter


if __name__ == '__main__':
    from dotenv import load_dotenv

    load_dotenv()

