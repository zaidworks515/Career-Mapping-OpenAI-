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

smtp_host = os.getenv("SMTP_HOST")
smtp_port = os.getenv("SMTP_PORT")
smtp_email = os.getenv("SMTP_EMAIL")
smtp_password = os.getenv("SMTP_PASSWORD")
admin_email = os.getenv("ADMIN_EMAIL")



