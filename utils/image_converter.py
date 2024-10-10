import os
import base64


def image_to_base64(question_id):
    image_path = os.path.join(os.getenv('ROOT_FOLDER'), f"data/questions_images/{question_id}.png")

    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    return base64_image


def image_to_base64_2(src: str):
    print(src)
    image_path = os.path.join(os.getenv('ROOT_FOLDER'), src)

    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    return base64_image
