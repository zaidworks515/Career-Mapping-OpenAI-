from dotenv import load_dotenv
import os

env = load_dotenv()
cv_path = os.getenv('CV_PATH')
port = os.getenv('PORT')
key = os.getenv('KEY')
openapi_key = os.getenv('OPENAPI')
node_server_url = os.getenv('NodeServerURL')

host = os.getenv('HOST')
user = os.getenv('USER')
password = os.getenv('PASSWORD')
database = os.getenv('DATABASE')


