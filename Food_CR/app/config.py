import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is not set")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PAGE_SIZE = 4
    FIREBASE_VAPID_KEY = os.getenv("FIREBASE_VAPID_KEY")


class DevConfig(Config):
    DEBUG = True


class ProdConfig(Config):
    DEBUG = False


class TestConfig(Config):
    TESTING = True


config_map = {
    'dev': DevConfig,
    'prod': ProdConfig,
    'test': TestConfig,
}
