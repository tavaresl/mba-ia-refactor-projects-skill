from flask import Blueprint, jsonify, request

from controllers import task_controller
from routes.common import read_json

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify(task_controller.list_tasks()), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    return jsonify(task_controller.get_task(task_id)), 200


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    return jsonify(task_controller.create_task(read_json())), 201


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    # o controller busca a task antes de ler o corpo (404 antes de 400), como no original
    return jsonify(task_controller.update_task(task_id, read_json)), 200


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    return jsonify(task_controller.delete_task(task_id)), 200


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    results = task_controller.search_tasks(
        request.args.get('q', ''),
        request.args.get('status', ''),
        request.args.get('priority', ''),
        request.args.get('user_id', ''),
    )
    return jsonify(results), 200


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    return jsonify(task_controller.task_stats()), 200
