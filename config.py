import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 基础设置
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))

# 文件路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
TEMPLATE_FOLDER = os.path.join(BASE_DIR, 'templates')

# API密钥
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
HF_API_KEY = os.getenv('HF_API_KEY', '')
AZURE_SPEECH_KEY = os.getenv('AZURE_SPEECH_KEY', '')
AZURE_SPEECH_REGION = os.getenv('AZURE_SPEECH_REGION', 'eastasia')
TENCENT_SECRET_ID = os.getenv('TENCENT_SECRET_ID', '')
TENCENT_SECRET_KEY = os.getenv('TENCENT_SECRET_KEY', '')

# 图像生成参数
IMAGE_WIDTH = int(os.getenv('IMAGE_WIDTH', 768))
IMAGE_HEIGHT = int(os.getenv('IMAGE_HEIGHT', 512))
DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'runwayml/stable-diffusion-v1-5')

# 视频生成参数
FPS = int(os.getenv('FPS', 24))
VIDEO_CODEC = os.getenv('VIDEO_CODEC', 'libx264')
AUDIO_CODEC = os.getenv('AUDIO_CODEC', 'aac')

# 默认语音
DEFAULT_VOICE = os.getenv('DEFAULT_VOICE', 'zh-CN-XiaoxiaoNeural')

# 漫画风格
COMIC_STYLES = {
    'default': '默认漫画风格',
    'anime': '动漫风格',
    'realistic': '写实风格',
    'watercolor': '水彩风格',
    'sketch': '素描风格'
}

# 风格提示词
STYLE_PROMPTS = {
    'default': ', comic style, detailed, vibrant colors',
    'anime': ', anime style, manga, detailed, vibrant colors',
    'realistic': ', realistic style, detailed, photorealistic',
    'watercolor': ', watercolor style, artistic, soft colors',
    'sketch': ', sketch style, pencil drawing, black and white'
}

# 风格负面提示词
STYLE_NEGATIVE_PROMPTS = {
    'default': 'blurry, low quality, distorted, deformed',
    'anime': 'blurry, low quality, distorted, deformed, photorealistic',
    'realistic': 'cartoon, anime, sketch, drawing, blurry',
    'watercolor': 'digital art, sharp edges, blurry, low quality',
    'sketch': 'color, painting, digital art, blurry, low quality'
}

# 系统限制
MAX_TEXT_LENGTH = int(os.getenv('MAX_TEXT_LENGTH', 5000))
CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', 3600))  # 1小时
TASK_TIMEOUT = int(os.getenv('TASK_TIMEOUT', 600))  # 10分钟

# 环境配置类
class Config:
    DEBUG = False
    TESTING = False
    SECRET_KEY = SECRET_KEY

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

# 配置映射
config_by_name = {
    'dev': DevelopmentConfig,
    'test': TestingConfig,
    'prod': ProductionConfig
}

# 获取当前配置
def get_config():
    env = os.getenv('FLASK_ENV', 'dev')
    return config_by_name.get(env, DevelopmentConfig)
