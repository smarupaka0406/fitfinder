import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///fitFinder.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/tmp/fitFinder_uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    MAX_RESULTS = int(os.getenv('MAX_RESULTS', 20))
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.6))
