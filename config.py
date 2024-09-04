from dotenv import load_dotenv
import os


env =load_dotenv()
cv_path = os.getenv('CV_PATH')
port = os.getenv('PORT')
key = os.getenv('KEY')
openapi_key = os.getenv('OPENAPI')

