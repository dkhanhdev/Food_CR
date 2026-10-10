from flask import Blueprint
from app.controllers.reviewController import ReviewController
from app.middleware import role_required
from app.models.model import UserRole

review_api = Blueprint('review_api', __name__)

# ==================== CREATE & UPDATE ====================

# POST /api/reviews - Submit new review
review_api.add_url_rule(
    '',
    view_func=role_required(UserRole.CUSTOMER)(ReviewController.submit_review),
    methods=['POST']
)

# PATCH /api/reviews/<review_id> - Update review (rating & comment)
review_api.add_url_rule(
    '/<int:review_id>',
    view_func=role_required(UserRole.CUSTOMER)(ReviewController.update_review),
    methods=['PATCH']
)

# DELETE /api/reviews/<review_id> - Delete review
review_api.add_url_rule(
    '/<int:review_id>',
    view_func=role_required(UserRole.CUSTOMER)(ReviewController.delete_review),
    methods=['DELETE']
)

# ==================== READ ====================

# GET /api/reviews/<review_id> - Get single review
review_api.add_url_rule(
    '/<int:review_id>',
    view_func=ReviewController.get_review_detail,
    methods=['GET']
)

# GET /api/me/reviews - Get current user's reviews
review_api.add_url_rule(
    '/me',
    view_func=role_required(UserRole.CUSTOMER)(ReviewController.get_my_reviews),
    methods=['GET'],
    endpoint='get_my_reviews'
)

# GET /api/restaurants/<restaurant_id>/reviews - Get reviews by restaurant
review_api.add_url_rule(
    '/restaurants/<int:restaurant_id>',
    view_func=ReviewController.get_restaurant_reviews,
    methods=['GET'],
    endpoint='get_restaurant_reviews'
)

# GET /api/restaurants/<restaurant_id>/rating-summary - Get rating stats
review_api.add_url_rule(
    '/restaurants/<int:restaurant_id>/rating-summary',
    view_func=ReviewController.get_restaurant_rating_summary,
    methods=['GET'],
    endpoint='get_rating_summary'
)

# GET /api/me/restaurants/<restaurant_id>/review - Check user review for restaurant
review_api.add_url_rule(
    '/me/restaurants/<int:restaurant_id>',
    view_func=ReviewController.get_user_restaurant_review,
    methods=['GET'],
    endpoint='get_user_restaurant_review'
)

# GET /api/reviews/eligibility/restaurants/<restaurant_id> - Check if user can
# review this restaurant right now + list their COMPLETED orders here
review_api.add_url_rule(
    '/eligibility/restaurants/<int:restaurant_id>',
    view_func=ReviewController.get_review_eligibility,
    methods=['GET'],
    endpoint='get_review_eligibility'
)
