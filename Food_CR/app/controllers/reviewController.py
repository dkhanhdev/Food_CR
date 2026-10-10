import cloudinary.uploader
from flask import request, jsonify
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.dao.reviewDao import ReviewDao
from app.models.model import UserRole


class ReviewController:
    """Controller for restaurant review operations"""

    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

    @staticmethod
    def _allowed_file(filename):
        """Check if file extension is allowed"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ReviewController.ALLOWED_EXTENSIONS

    @staticmethod
    def _upload_image_to_cloudinary(file):
        """
        Upload image to Cloudinary
        
        Returns:
            (success, url_or_error_message)
        """
        try:
            # Validate file exists and has size
            if not file or file.filename == '':
                return False, "Không có tệp được chọn"
            
            # Validate extension
            if not ReviewController._allowed_file(file.filename):
                return False, "Chỉ hỗ trợ JPG, PNG, WebP"
            
            # Validate file size
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset
            
            if file_size > ReviewController.MAX_FILE_SIZE:
                return False, "Tệp quá lớn (tối đa 5MB)"
            
            # Upload to Cloudinary
            secure_name = secure_filename(file.filename)
            result = cloudinary.uploader.upload(
                file,
                folder='khm_foodie_reviews',
                resource_type='auto',
                public_id=f"review_{current_user.id}_{int(__import__('time').time())}"
            )
            
            return True, result.get('secure_url')
        except Exception as e:
            return False, f"Lỗi tải ảnh: {str(e)}"

    @staticmethod
    @login_required
    def submit_review():
        """
        POST /api/reviews
        Submit new review for restaurant
        
        Body:
        {
            "restaurant_id": 1,
            "order_id": 123,
            "rating": 5,
            "comment": "Món ăn rất ngon!",
            "images": [file, file, ...]  # multipart/form-data
        }
        """
        try:
            # Get form data
            restaurant_id = request.form.get('restaurant_id', type=int)
            order_id = request.form.get('order_id', type=int)
            rating = request.form.get('rating')
            comment = request.form.get('comment', '').strip()
            
            # Validate required fields
            if not restaurant_id:
                return jsonify({
                    "success": False,
                    "message": "Thiếu restaurant_id"
                }), 400
            
            if not rating:
                return jsonify({
                    "success": False,
                    "message": "Thiếu rating"
                }), 400
            
            # Create review
            success, data = ReviewDao.create_review(
                user_id=current_user.id,
                restaurant_id=restaurant_id,
                rating=rating,
                comment=comment if comment else None,
                order_id=order_id
            )
            
            if not success:
                return jsonify({
                    "success": False,
                    "message": data
                }), 400
            
            review_id = data['id']
            
            # Upload images if provided
            image_urls = []
            images = request.files.getlist('images')
            
            if images:
                for image_file in images:
                    if image_file and image_file.filename != '':
                        success, result = ReviewController._upload_image_to_cloudinary(image_file)
                        if success:
                            image_urls.append(result)
                        else:
                            # Log error but continue with other images
                            print(f"Image upload failed: {result}")
                
                # Add images to review
                if image_urls:
                    success, img_data = ReviewDao.add_review_images(review_id, image_urls)
                    if success:
                        data['images'] = img_data['images']
            
            # Commit all changes
            from app.extensions import db
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "Đánh giá đã được gửi thành công",
                "data": data
            }), 201
        
        except Exception as e:
            from app.extensions import db
            db.session.rollback()
            return jsonify({
                "success": False,
                "message": f"Lỗi server: {str(e)}"
            }), 500

    @staticmethod
    def get_restaurant_reviews(restaurant_id):
        """
        GET /api/restaurants/<restaurant_id>/reviews
        Get reviews for restaurant with pagination

        Query params:
            - limit: 10 (default)
            - offset: 0 (default)
            - sort: newest|oldest|rating_high|rating_low
        """
        try:
            limit = request.args.get('limit', 10, type=int)
            offset = request.args.get('offset', 0, type=int)
            sort_by = request.args.get('sort', 'newest')
            
            # Validate pagination
            limit = min(limit, 50)  # Max 50 per page
            offset = max(offset, 0)
            
            # Get reviews
            result = ReviewDao.get_reviews_by_restaurant(
                restaurant_id=restaurant_id,
                limit=limit,
                offset=offset,
                sort_by=sort_by
            )
            
            return jsonify({
                "success": True,
                "data": {
                    "restaurant_id": restaurant_id,
                    "reviews": result['reviews'],
                    "pagination": {
                        "total": result['total'],
                        "limit": limit,
                        "offset": offset,
                        "has_more": result['has_more']
                    }
                }
            }), 200
        
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Lỗi: {str(e)}"
            }), 500

    @staticmethod
    @login_required
    def get_my_reviews():
        """
        GET /api/me/reviews
        Get current user's reviews
        
        Query params:
            - limit: 10 (default)
            - offset: 0 (default)
        """
        try:
            limit = request.args.get('limit', 10, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            limit = min(limit, 50)
            offset = max(offset, 0)
            
            result = ReviewDao.get_reviews_by_user(
                user_id=current_user.id,
                limit=limit,
                offset=offset
            )
            
            return jsonify({
                "success": True,
                "data": {
                    "reviews": result['reviews'],
                    "pagination": {
                        "total": result['total'],
                        "limit": limit,
                        "offset": offset,
                        "has_more": result['has_more']
                    }
                }
            }), 200
        
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Lỗi: {str(e)}"
            }), 500

    @staticmethod
    def get_review_detail(review_id):
        """
        GET /api/reviews/<review_id>
        Get single review with images
        """
        try:
            review = ReviewDao.get_review_by_id(review_id)
            if not review:
                return jsonify({
                    "success": False,
                    "message": "Không tìm thấy đánh giá"
                }), 404
            
            return jsonify({
                "success": True,
                "data": review
            }), 200
        
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Lỗi: {str(e)}"
            }), 500

    @staticmethod
    @login_required
    def update_review(review_id):
        """
        PATCH /api/reviews/<review_id>
        Update review (rating and comment only)

        Body:
        {
            "rating": 4,
            "comment": "Chỉnh sửa: Khá ngon"
        }
        """
        try:
            data = request.get_json() or {}
            
            # Check ownership
            review = ReviewDao.get_review_by_id(review_id)
            if not review:
                return jsonify({
                    "success": False,
                    "message": "Không tìm thấy đánh giá"
                }), 404
            
            if review['user_id'] != current_user.id:
                return jsonify({
                    "success": False,
                    "message": "Bạn không có quyền chỉnh sửa đánh giá này"
                }), 403
            
            # Update
            success, result = ReviewDao.update_review(
                review_id=review_id,
                rating=data.get('rating'),
                comment=data.get('comment')
            )
            
            if not success:
                return jsonify({
                    "success": False,
                    "message": result
                }), 400
            
            return jsonify({
                "success": True,
                "message": "Cập nhật thành công",
                "data": result
            }), 200
        
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Lỗi: {str(e)}"
            }), 500

    @staticmethod
    @login_required
    def delete_review(review_id):
        """
        DELETE /api/reviews/<review_id>
        Delete review (soft delete)
        """
        try:
            # Check ownership
            review = ReviewDao.get_review_by_id(review_id)
            if not review:
                return jsonify({
                    "success": False,
                    "message": "Không tìm thấy đánh giá"
                }), 404
            
            if review['user_id'] != current_user.id and current_user.role != UserRole.ADMIN:
                return jsonify({
                    "success": False,
                    "message": "Bạn không có quyền xóa đánh giá này"
                }), 403
            
            success, message = ReviewDao.delete_review(review_id, soft_delete=True)
            
            if not success:
                return jsonify({
                    "success": False,
                    "message": message
                }), 400
            
            return jsonify({
                "success": True,
                "message": message
            }), 200
        
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Lỗi: {str(e)}"
            }), 500

    @staticmethod
    def get_restaurant_rating_summary(restaurant_id):
        """
        GET /api/restaurants/<restaurant_id>/rating-summary
        Get rating statistics for restaurant

        Returns:
        {
            "average_rating": 4.5,
            "total_reviews": 150,
            "distribution": {
                "5": 100,
                "4": 30,
                ...
            }
        }
        """
        try:
            summary = ReviewDao.get_restaurant_rating_summary(restaurant_id)
            
            return jsonify({
                "success": True,
                "data": summary
            }), 200
        
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Lỗi: {str(e)}"
            }), 500

    @staticmethod
    def get_review_eligibility(restaurant_id):
        """
        GET /api/reviews/eligibility/restaurants/<restaurant_id>
        Check if current user can review this restaurant right now, and
        return their COMPLETED orders here so the UI can render an order
        picker. This is the endpoint the "write review" section should
        check before showing the form.

        Returns:
        {
            "authenticated": true,
            "has_reviewed": false,
            "can_review": true,
            "completed_orders": [
                {"id": 12, "name": "DH-00012", "created_at": "...", "total_amount": 120000},
                ...
            ]
        }
        """
        try:
            if not current_user.is_authenticated:
                return jsonify({
                    "success": True,
                    "data": {
                        "authenticated": False,
                        "has_reviewed": False,
                        "can_review": False,
                        "completed_orders": []
                    }
                }), 200

            result = ReviewDao.get_review_eligibility(
                user_id=current_user.id,
                restaurant_id=restaurant_id
            )
            result["authenticated"] = True

            return jsonify({
                "success": True,
                "data": result
            }), 200

        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Lỗi: {str(e)}"
            }), 500

    @staticmethod
    def get_user_restaurant_review(restaurant_id):
        """
        GET /api/me/restaurants/<restaurant_id>/review
        Check if current user has review for restaurant

        Returns:
        {
            "has_review": true,
            "review": {...} or null
        }
        """
        try:
            if not current_user.is_authenticated:
                return jsonify({
                    "success": True,
                    "data": {
                        "has_review": False,
                        "review": None
                    }
                }), 200

            review = ReviewDao.get_user_review_for_restaurant(
                user_id=current_user.id,
                restaurant_id=restaurant_id
            )
            
            return jsonify({
                "success": True,
                "data": {
                    "has_review": review is not None,
                    "review": review
                }
            }), 200
        
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Lỗi: {str(e)}"
            }), 500
