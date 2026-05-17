
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.sql import text
from Recs.defect_model import DefectClass, DeleteInspectionsRequest
from Recs.sqlAlch import Inspection, Base
from Recs.settings import IMAGE_FOLDER, OUTPUT_FOLDER_IMG, OUTPUT_FOLDER_JSON, MODEL_PATH, CLASSES, local
import os
import asyncio
import json
import logging

# Создание FastAPI приложения
app = FastAPI()

# Подключение директории с изображениями как статических файлов
app.mount("/out", StaticFiles(directory="out"), name="out")

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Настройка базы данных
DATABASE_URL = "postgresql+asyncpg://postgres:12321@localhost:5432/pcb_defects"
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lifespan для управления жизненным циклом приложения
@asynccontextmanager
async def lifespan(app):
    logger.info("Запуск приложения, инициализация базы данных")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    logger.info("Завершение работы приложения, закрытие соединения с базой")
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

# Подключение директории с изображениями как статических файлов
app.mount("/out", StaticFiles(directory="out"), name="out")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Хранение активных соединений WebSocket
active_connections = set()

# Последнее отправленное изображение
last_image = None

# Подключение по WebSocket
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    logger.info("Достигнут WebSocket endpoint")
    await websocket.accept()
    logger.info(f"WebSocket принят, клиент: {websocket.client}")
    active_connections.add(websocket)
    try:
        global last_image
        logger.info(f"WebSocket подключен, last_image: {last_image}, OUTPUT_FOLDER_IMG: {OUTPUT_FOLDER_IMG}")
        # При подключении отправляем последнее изображение, если оно есть
        if last_image:
            image_path = os.path.join(OUTPUT_FOLDER_IMG, last_image)
            logger.info(f"Проверка last_image: {image_path}, существует: {os.path.exists(image_path)}")
            if os.path.exists(image_path):
                await send_img(last_image, websocket)
            else:
                logger.warning(f"Последнее изображение не найдено: {image_path}")
        
        # Проверка папки с изображениями каждые 2 секунды
        while True:
            if not active_connections:
                logger.info("Нет активных соединений, выход из цикла")
                break
            try:
                files = [f for f in os.listdir(OUTPUT_FOLDER_IMG) if os.path.isfile(os.path.join(OUTPUT_FOLDER_IMG, f))]
                if files:
                    newest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(OUTPUT_FOLDER_IMG, f)))
                    if last_image != newest_file:
                        logger.info(f"Обнаружен новый файл: {newest_file}")
                        await send_img(newest_file)
                        last_image = newest_file
                else:
                    logger.debug("Нет файлов в OUTPUT_FOLDER_IMG")
                await asyncio.sleep(2)  # Уменьшено до 2 секунд
            except Exception as e:
                logger.error(f"Ошибка при проверке файлов: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Ошибка в WebSocket: {e}", exc_info=True)
    finally:
        logger.info(f"WebSocket отключен, клиент: {websocket.client}")
        active_connections.discard(websocket)

# Функция отправки изображения и данных о дефектах по WebSocket
async def send_img(image_url: str, websocket: WebSocket = None):
    logger.info(f"Вызвана функция send_img с файлом: {image_url}")
    json_url = os.path.join(OUTPUT_FOLDER_JSON, f"{os.path.splitext(image_url)[0]}.json")
    image_path = os.path.join(OUTPUT_FOLDER_IMG, image_url)
    
    logger.info(f"Проверка путей: image_path={image_path}, существует: {os.path.exists(image_path)}")
    logger.info(f"Проверка путей: json_url={json_url}, существует: {os.path.exists(json_url)}")
    
    if not os.path.exists(image_path) or not os.path.exists(json_url):
        logger.warning(f"Файлы не найдены: image_path={image_path}, json_url={json_url}")
        return
    
    try:
        with open(json_url, "r", encoding='utf-8') as json_file:
            defect_data = json.load(json_file)
        logger.info(f"Загружены дефекты: {defect_data}")
        
        try:
            defects = DefectClass(defects=defect_data)  # Валидация структуры данных
            image_url = os.path.join(local, image_url)
            data = {"image": image_url, "defects": defect_data}
            logger.info(f"Подготовлены данные для отправки: {data}")
            
            to_remove = set()
            connections_to_send = [websocket] if websocket else list(active_connections)
            for connection in connections_to_send:
                if connection in active_connections:
                    try:
                        await connection.send_json(data)
                        logger.info(f"Отправлено сообщение клиенту: {connection.client}")
                    except Exception as e:
                        logger.error(f"Ошибка отправки клиенту {connection.client}: {e}")
                        if websocket is None:
                            to_remove.add(connection)
            for connection in to_remove:
                active_connections.discard(connection)
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"Ошибка валидации файла {json_url}: {e}")
    except Exception as e:
        logger.error(f"Ошибка при обработке JSON {json_url}: {e}", exc_info=True)

# Получение всех записей из базы данных
@app.get("/database")
async def get_all_inspections(session: AsyncSession = Depends(get_session)):
    logger.info("Запрос к /database")
    async with session as sess:
        try:
            result = await session.execute(text("SELECT * FROM inspections"))
            inspections = result.fetchall()
            inspections_list = [
                {
                    "id": row[0],
                    "filename": row[1],
                    "image_path": row[2],
                    "defects": row[3],
                    "timestamp": row[4] if isinstance(row[4], str) else row[4].isoformat()
                }
                for row in inspections
            ]
            logger.info(f"Получено {len(inspections_list)} записей из таблицы inspections")
            return inspections_list
        except Exception as e:
            logger.error(f"Ошибка при получении inspections: {e}", exc_info=True)
            raise

# Удаление записей по ID, полученным от клиента
@app.delete("/inspections")
async def delete_inspections(request: DeleteInspectionsRequest, session: AsyncSession = Depends(get_session)):
    logger.info(f"Запрос на удаление inspections с IDs: {request.ids}")
    try:
        for id in request.ids:
            await session.execute(text("DELETE FROM inspections WHERE id = :id"), {"id": id})
        await session.commit()
        logger.info("Записи успешно удалены")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Ошибка при удалении inspections: {e}", exc_info=True)
        await session.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/health")
async def health_check():
    logger.info("Request to /health")
    return {"status": "ok"}