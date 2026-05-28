from .defect_model import DefectClass
from ultralytics import YOLO
from .settings import IMAGE_FOLDER, OUTPUT_FOLDER_IMG, OUTPUT_FOLDER_JSON, MODEL_PATH, CLASSES
from .database import get_session
from .sqlAlch import Inspection
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import asyncio
import json
import cv2
import os

model = YOLO(MODEL_PATH)  # загрузка модели
print(model.names)

async def process_images():
    while True:
        for filename in os.listdir(IMAGE_FOLDER):
            if filename.endswith((".jpg", ".png", ".JPG")):


                image_path = os.path.join(IMAGE_FOLDER, filename)
                img = cv2.imread(image_path)

                results = model(img)
                print(model.device)
                detections = results[0].boxes.data.tolist()

                defect_counts = {}

                for i in range(len(detections)):
                    # Перестановка координат
                    temp = detections[i][1]
                    detections[i][1] = detections[i][2]
                    detections[i][2] = temp

                    # Формирование точек для полигона
                    points = []
                    for j in range(2):
                        for k in range(2, 4):
                            points.append([detections[i][j], detections[i][k]])

                    points[2], points[3] = points[3], points[2]

                    defect_type = CLASSES[int(detections[i][5])]
                    defect_counts[defect_type] = defect_counts.get(defect_type, 0) + 1

                    box = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
                    cv2.polylines(img, [box], isClosed=True, color=(0, 255, 0), thickness=2)
                    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                    draw = ImageDraw.Draw(pil_img)

                    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)

                    draw.text(
                        (int(points[0][0]), int(points[0][1]) - 30),
                        defect_type,
                        font=font,
                        fill=(0, 255, 0)
                    )

                    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

                # Удаляем исходное изображение
                os.remove(image_path)

                # Сохраняем обработанное изображение
                output_path = os.path.join(OUTPUT_FOLDER_IMG, filename)
                cv2.imwrite(output_path, img)

                # === СОХРАНЕНИЕ РЕЗУЛЬТАТОВ ===
                try:
                    # Валидируем дефекты
                    DefectClass(defects=defect_counts)

                    # Сохраняем JSON
                    json_path = os.path.join(OUTPUT_FOLDER_JSON, filename.rsplit(".", 1)[0] + ".json")
                    with open(json_path, "w", encoding="utf-8") as json_file:
                        json.dump(defect_counts, json_file, indent=4, ensure_ascii=False)

                    # === ЗАПИСЬ В БД С ИСПОЛЬЗОВАНИЕМ async FOR ===
                    async for session in get_session():
                        inspection = Inspection(
                            filename=filename,
                            image_path=output_path,
                            defects=defect_counts
                        )
                        session.add(inspection)
                        await session.commit()
                        break   # ОБЯЗАТЕЛЬНО — иначе генератор продолжит бесконечно

                except ValueError:
                    print("Invalid Value")

        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(process_images())
