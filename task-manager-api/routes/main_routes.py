from datetime import datetime

from flask import Blueprint

main_bp = Blueprint('main', __name__)


@main_bp.route('/health')
def health():
    return {'status': 'ok', 'timestamp': str(datetime.now())}


@main_bp.route('/')
def index():
    return {'message': 'Task Manager API', 'version': '1.0'}
