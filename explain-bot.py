import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
from bs4 import BeautifulSoup
from readability import Document
import ollama
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from googleapiclient.discovery import build
import re

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TELEGRAM_TOKEN = "8046244586:AAEwmDRAlBWnZdP9nvV6TuFmSwxzARlRgOM"
YOUTUBE_API_KEY = "AIzaSyBzjSU0Kso-dj24JFO60WhUnMssUFHeDHs"  # Получить: https://console.cloud.google.com/
MAX_TEXT_LENGTH = 4000

# Проверка YouTube-ссылки
def is_youtube_url(url: str) -> bool:
    youtube_pattern = r'(https?://)?(www\.)?(youtube|youtu)\.(com|be)'
    return re.match(youtube_pattern, url) is not None

# Извлечение ID видео
def get_video_id(url: str) -> str:
    if "youtu.be" in url:
        return url.split("/")[-1].split("?")[0]
    parsed = urlparse(url)
    if parsed.netloc == "youtube.com" or parsed.netloc == "www.youtube.com":
        return parse_qs(parsed.query).get("v", [""])[0]
    return ""

# Получение субтитров
def get_youtube_transcript(video_id: str) -> str:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["ru", "en"])
        return " ".join([entry["text"] for entry in transcript])
    except Exception as e:
        logger.error(f"Ошибка субтитров: {str(e)}")
        return ""

# Получение метаданных YouTube
def get_youtube_metadata(video_id: str) -> str:
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        request = youtube.videos().list(
            part="snippet",
            id=video_id
        )
        response = request.execute()
        
        if not response['items']:
            return ""
            
        snippet = response['items'][0]['snippet']
        metadata = [
            f"Название: {snippet['title']}",
            f"Автор: {snippet['channelTitle']}",
            f"Описание: {snippet['description'][:500]}..."
        ]
        return "\n".join(metadata)
    except Exception as e:
        logger.error(f"Ошибка метаданных: {str(e)}")
        return ""

# Парсинг обычных сайтов
def extract_website_text(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        doc = Document(response.text)
        soup = BeautifulSoup(doc.summary(), "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        return text if text else "Не удалось извлечь текст."
    except Exception as e:
        return f"Ошибка: {str(e)}"

# Основная функция извлечения текста
def extract_text(url: str) -> str:
    if is_youtube_url(url):
        video_id = get_video_id(url)
        if not video_id:
            return "Ошибка: Не удалось распознать ID видео."
        
        # Пробуем получить субтитры
        transcript = get_youtube_transcript(video_id)
        if transcript:
            return transcript
            
        # Если субтитров нет, получаем метаданные
        metadata = get_youtube_metadata(video_id)
        if metadata:
            return f"Видео без субтитров. Доступная информация:\n\n{metadata}"
            
        return "Ошибка: Не удалось получить информацию о видео."
    
    # Для обычных сайтов
    return extract_website_text(url)

# Генерация объяснения
def explain_with_ai(text: str) -> str:
    prompt = f"""
    Объясни этот текст ровно 144 словами на русском языке. Будь точен и краток.
    Если это видео без субтитров - сделай вывод на основе названия и описания.
    Текст: {text[:10000]}
    """
    try:
        response = ollama.generate(
            model="granite3.3:2b",
            prompt=prompt,
            options={"temperature": 0.1, "num_predict": 150}
        )
        words = response["response"].split()
        return " ".join(words[:100])
    except Exception as e:
        return f"Ошибка ИИ: {str(e)}"

# Обработчики Telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔍 Привет! Отправь мне ссылку на статью или YouTube-видео, "
        "и я объясню её содержание ровно 100 словами.\n\n"
        "Примеры:\n"
        "• https://ru.wikipedia.org/wiki/Искусственный_интеллект\n"
        "• https://youtu.be/dQw4w9WgXcQ"
    )

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("❌ Это не ссылка. Попробуйте ещё раз.")
        return

    await update.message.reply_text("⏳ Анализирую...")
    
    try:
        text = extract_text(url)
        if not text or "Ошибка" in text:
            await update.message.reply_text(text if text else "Не удалось обработать ссылку.")
            return

        explanation = explain_with_ai(text)
        await update.message.reply_text(f"📚 Объяснение (100 слов):\n\n{explanation}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Критическая ошибка: {str(e)}")

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.run_polling()

if __name__ == "__main__":
    main()