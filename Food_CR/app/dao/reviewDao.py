from datetime import datetime, timedelta
from sqlalchemy import desc, func
from flask_login import current_user

from app.extensions import db
from app.models.model import Review, ReviewImage, Order, Status, Restaurant, User


class ReviewDao:
    """Data Access Object for Review and ReviewImage operations"""

    @staticmethod
    def get_completed_orders(user_id, restaurant_id):
        """
        Get all COMPLETED orders of a user at a restaurant, newest first.
        This is the single source of truth for review eligibility — it is
        always looked up server-side and never trusts a client-supplied
        order_id as proof of eligibility.
        """
        return Order.query.filter_by(
            user_id=user_id,
            restaurant_id=restaurant_id,
            status=Status.COMPLETED
        ).order_by(desc(Order.created_at)).all()

    @staticmethod
    def validate_can_review(user_id, restaurant_id, order_id=None):
        """
        Validate if user can submit review for restaurant.

        IMPORTANT: eligibility ("has a COMPLETED order at this restaurant")
        is always checked independently of order_id — order_id is only used
        (when valid) to record which order the review is tracking. A client
        that omits order_id, or sends a bogus one, can no longer skip the
        COMPLETED-order requirement.

        Returns:
            (True, resolved_order_id) on success
            (False, error_message) on failure
        """
        # Check if user already reviewed this restaurant
        existing_review = Review.query.filter_by(
            user_id=user_id,
            restaurant_id=restaurant_id
        ).first()

        if existing_review:
            return False, "Bạn đã đánh giá nhà hàng này rồi"

        # Always resolve eligibility from the DB — never trust order_id alone
        completed_orders = ReviewDao.get_completed_orders(user_id, restaurant_id)

        if not completed_orders:
            return False, "Bạn cần hoàn thành ít nhất 1 đơn hàng tại nhà hàng này trước khi có thể đánh giá"

        if order_id:
            matched = next((o for o in completed_orders if o.id == order_id), None)
            if not matched:
                return False, "Đơn hàng không hợp lệ hoặc chưa hoàn thành tại nhà hàng này"
            resolved_order_id = matched.id
        else:
            # No order chosen by the client: fall back to the most recent
            # COMPLETED order so the review still tracks a real order.
            resolved_order_id = completed_orders[0].id

        return True, resolved_order_id

    @staticmethod
    def get_review_eligibility(user_id, restaurant_id):
        """
        Check whether a user can review a restaurant right now, and list
        their COMPLETED orders there (for a UI order picker).

        Returns:
            {
                "has_reviewed": bool,
                "can_review": bool,
                "completed_orders": [{"id", "name", "created_at", "total_amount"}, ...]
            }
        """
        existing_review = Review.query.filter_by(
            user_id=user_id,
            restaurant_id=restaurant_id
        ).first()

        completed_orders = ReviewDao.get_completed_orders(user_id, restaurant_id)

        orders_data = [
            {
                "id": o.id,
                "name": o.name,
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "total_amount": float(o.total_amount) if o.total_amount is not None else None,
            }
            for o in completed_orders
        ]

        return {
            "has_reviewed": existing_review is not None,
            "can_review": existing_review is None and len(orders_data) > 0,
            "completed_orders": orders_data,
        }

    @staticmethod
    def validate_rating(rating):
        """Validate rating value (1-5)"""
        try:
            rating_int = int(rating)
            if rating_int < 1 or rating_int > 5:
                return False, "Đánh giá phải từ 1 đến 5 sao"
            return True, None
        except (ValueError, TypeError):
            return False, "Đánh giá không hợp lệ"

    @staticmethod
    def validate_comment(comment):
        """Validate comment length"""
        if not comment or comment.strip() == "":
            # Comment is optional
            return True, None
        
        comment = comment.strip()
        if len(comment) < 10:
            return False, "Nhận xét phải tối thiểu 10 ký tự"
        
        if len(comment) > 1000:
            return False, "Nhận xét tối đa 1000 ký tự"
        
        return True, None

    @staticmethod
    def create_review(user_id, restaurant_id, rating, comment=None, order_id=None):
        """
        Create new review for restaurant
        
        Args:
            user_id: Customer ID
            restaurant_id: Restaurant ID
            rating: Rating (1-5)
            comment: Optional comment text
            order_id: Optional order ID
            
        Returns:
            (success, data_or_error_message)
        """
        # Validate rating
        is_valid, error_msg = ReviewDao.validate_rating(rating)
        if not is_valid:
            return False, error_msg
        
        # Validate comment if provided
        is_valid, error_msg = ReviewDao.validate_comment(comment)
        if not is_valid:
            return False, error_msg
        
        # Validate user can review (also resolves the order_id to record,
        # regardless of what the client sent)
        is_valid, result = ReviewDao.validate_can_review(user_id, restaurant_id, order_id)
        if not is_valid:
            return False, result
        resolved_order_id = result

        try:
            # Create review
            review = Review(
                user_id=user_id,
                restaurant_id=restaurant_id,
                order_id=resolved_order_id,
                rating=int(rating),
                comment=comment.strip() if comment else None,
                active=True
            )
            
            db.session.add(review)
            db.session.flush()  # Get review ID before commit
            
            return True, {
                "id": review.id,
                "user_id": review.user_id,
                "restaurant_id": review.restaurant_id,
                "rating": review.rating,
                "comment": review.comment,
                "created_at": review.created_at.isoformat() if review.created_at else None
            }
        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi tạo đánh giá: {str(e)}"

    @staticmethod
    def add_review_images(review_id, image_urls):
        """
        Add images to review
        
        Args:
            review_id: Review ID
            image_urls: List of Cloudinary URLs
            
        Returns:
            (success, data_or_error_message)
        """
        if not image_urls:
            return True, {"images": []}
        
        # Validate list
        if not isinstance(image_urls, list):
            return False, "Images phải là một danh sách"
        
        # Max 5 images
        if len(image_urls) > 5:
            return False, "Tối đa 5 ảnh"
        
        try:
            added_images = []
            for url in image_urls:
                if not url or url.strip() == "":
                    continue
                
                image = ReviewImage(
                    review_id=review_id,
                    image_url=url.strip()
                )
                db.session.add(image)
                added_images.append({
                    "id": image.id,
                    "url": image.image_url
                })
            
            db.session.flush()
            return True, {"images": added_images, "count": len(added_images)}
        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi thêm ảnh: {str(e)}"

    @staticmethod
    def get_reviews_by_restaurant(restaurant_id, limit=10, offset=0, sort_by='newest'):
        """
        Get paginated reviews for restaurant
        
        Args:
            restaurant_id: Restaurant ID
            limit: Number of reviews per page
            offset: Pagination offset
            sort_by: 'newest', 'oldest', 'rating_high', 'rating_low'
            
        Returns:
            {
                "total": total_count,
                "reviews": [...],
                "has_more": boolean
            }
        """
        query = Review.query.filter_by(
            restaurant_id=restaurant_id,
            active=True
        )
        
        # Sorting
        if sort_by == 'oldest':
            query = query.order_by(Review.created_at.asc())
        elif sort_by == 'rating_high':
            query = query.order_by(desc(Review.rating), desc(Review.created_at))
        elif sort_by == 'rating_low':
            query = query.order_by(Review.rating, desc(Review.created_at))
        else:  # newest (default)
            query = query.order_by(desc(Review.created_at))
        
        total = query.count()
        reviews_data = query.offset(offset).limit(limit + 1).all()
        
        has_more = len(reviews_data) > limit
        reviews_data = reviews_data[:limit]
        
        reviews_list = []
        for review in reviews_data:
            reviews_list.append(ReviewDao._serialize_review(review))
        
        return {
            "total": total,
            "reviews": reviews_list,
            "has_more": has_more
        }

    @staticmethod
    def get_reviews_by_user(user_id, limit=10, offset=0):
        """
        Get all reviews by customer
        """
        query = Review.query.filter_by(
            user_id=user_id,
            active=True
        ).order_by(desc(Review.created_at))
        
        total = query.count()
        reviews_data = query.offset(offset).limit(limit + 1).all()
        
        has_more = len(reviews_data) > limit
        reviews_data = reviews_data[:limit]
        
        reviews_list = []
        for review in reviews_data:
            reviews_list.append(ReviewDao._serialize_review(review))
        
        return {
            "total": total,
            "reviews": reviews_list,
            "has_more": has_more
        }

    @staticmethod
    def get_review_by_id(review_id):
        """Get review by ID with images"""
        review = Review.query.filter_by(id=review_id, active=True).first()
        
        if not review:
            return None
        
        return ReviewDao._serialize_review(review)

    @staticmethod
    def get_user_review_for_restaurant(user_id, restaurant_id):
        """Get user's review for specific restaurant"""
        review = Review.query.filter_by(
            user_id=user_id,
            restaurant_id=restaurant_id,
            active=True
        ).first()
        
        if not review:
            return None
        
        return ReviewDao._serialize_review(review)

    @staticmethod
    def update_review(review_id, rating=None, comment=None):
        """
        Update review (rating and comment only)
        Can update within 7 days of creation
        """
        review = Review.query.filter_by(id=review_id, active=True).first()
        
        if not review:
            return False, "Không tìm thấy đánh giá"
        
        # Check if within 7 days
        days_elapsed = (datetime.utcnow() - review.created_at).days
        if days_elapsed > 7:
            return False, "Chỉ có thể chỉnh sửa đánh giá trong vòng 7 ngày"
        
        try:
            if rating is not None:
                is_valid, error_msg = ReviewDao.validate_rating(rating)
                if not is_valid:
                    return False, error_msg
                review.rating = int(rating)
            
            if comment is not None:
                is_valid, error_msg = ReviewDao.validate_comment(comment)
                if not is_valid:
                    return False, error_msg
                review.comment = comment.strip() if comment else None
            
            review.created_updated_at = datetime.utcnow()
            db.session.commit()
            
            return True, ReviewDao._serialize_review(review)
        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi cập nhật: {str(e)}"

    @staticmethod
    def delete_review(review_id, soft_delete=True):
        """
        Delete review (soft delete by default)
        
        Args:
            review_id: Review ID
            soft_delete: If True, mark as inactive; if False, hard delete
            
        Returns:
            (success, message)
        """
        review = Review.query.filter_by(id=review_id).first()
        
        if not review:
            return False, "Không tìm thấy đánh giá"
        
        try:
            if soft_delete:
                review.active = False
                review.created_updated_at = datetime.utcnow()
                db.session.commit()
                return True, "Xóa đánh giá thành công"
            else:
                db.session.delete(review)
                db.session.commit()
                return True, "Xóa đánh giá thành công"
        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi xóa đánh giá: {str(e)}"

    @staticmethod
    def get_restaurant_rating_summary(restaurant_id):
        """
        Get rating summary for restaurant
        
        Returns:
            {
                "average_rating": 4.5,
                "total_reviews": 150,
                "distribution": {
                    5: 100,
                    4: 30,
                    3: 15,
                    2: 3,
                    1: 2
                }
            }
        """
        reviews = Review.query.filter_by(
            restaurant_id=restaurant_id,
            active=True
        ).all()
        
        if not reviews:
            return {
                "average_rating": 0,
                "total_reviews": 0,
                "distribution": {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
            }
        
        # Calculate average
        total_rating = sum(r.rating for r in reviews)
        average_rating = round(total_rating / len(reviews), 1)
        
        # Distribution
        distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        for review in reviews:
            distribution[review.rating] += 1
        
        return {
            "average_rating": average_rating,
            "total_reviews": len(reviews),
            "distribution": distribution
        }

    @staticmethod
    def _serialize_review(review):
        """Helper: Serialize review object to dict"""
        user = User.query.get(review.user_id)
        restaurant = Restaurant.query.get(review.restaurant_id)
        
        images = []
        if review.images:
            images = [
                {
                    "id": img.id,
                    "url": img.image_url,
                    "uploaded_at": img.uploaded_at.isoformat() if img.uploaded_at else None
                }
                for img in review.images
            ]
        
        return {
            "id": review.id,
            "user_id": review.user_id,
            "user_name": user.name if user else "Ẩn danh",
            "user_avatar": user.avatar if user else None,
            "restaurant_id": review.restaurant_id,
            "restaurant_name": restaurant.name if restaurant else None,
            "order_id": review.order_id,
            "rating": review.rating,
            "comment": review.comment,
            "images": images,
            "created_at": review.created_at.isoformat() if review.created_at else None,
            "updated_at": review.created_updated_at.isoformat() if review.created_updated_at else None,
            "active": review.active
        }
