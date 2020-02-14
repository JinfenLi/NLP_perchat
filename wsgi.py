import os
from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

from perchat import create_app  # noqa
from perchat.extensions import socketio

app = create_app('production')

if __name__ == '__main__':
    socketio.run(app)