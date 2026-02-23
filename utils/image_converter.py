import os
import base64


def image_to_base64(image_type: str, question_id):
    image_path = 'temp'

    if image_type == "question":
        image_path = os.path.join(os.getenv('ROOT_FOLDER'), f"data/images/questions/{question_id}.png")
    elif image_type == "answer":
        image_path = os.path.join(os.getenv('ROOT_FOLDER'), f"data/images/answers/{question_id}.png")
    elif image_type == "temp":
        image_path = os.path.join(os.getenv('ROOT_FOLDER'), f"data/temp/{question_id}.png")

    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    return base64_image
