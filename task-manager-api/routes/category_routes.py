from flask import Blueprint, jsonify

from controllers import category_controller
from routes.common import read_json

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(category_controller.list_categories()), 200


@category_bp.route('/categories', methods=['POST'])
def create_category():
    return jsonify(category_controller.create_category(read_json())), 201


@category_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    return jsonify(category_controller.update_category(cat_id, read_json)), 200


@category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    return jsonify(category_controller.delete_category(cat_id)), 200
