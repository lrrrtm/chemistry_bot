import os
import base64


def image_to_base64(question_id):
    # Получаем путь к изображению
    image_path = os.path.join(os.getenv('ROOT_FOLDER'), f"data/questions_images/{question_id}.png")

    # Проверяем существование файла
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Изображение не найдено по пути: {image_path}")

    # Читаем изображение и конвертируем его в base64
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    return base64_image