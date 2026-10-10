from app.dao.restaurantsDao import RestaurantsDao
from flask import jsonify, request, render_template, redirect, url_for
from flask_login import current_user
from app.models.model import UserRole


class SearchController:

    @staticmethod
    def search_restaurants():
        keyword = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 9, type=int)

        restaurants_pagination = RestaurantsDao.search_restaurants(keyword, page, per_page)
        dishes_pagination = RestaurantsDao.search_dishes(keyword, page, per_page)

        restaurant_data = [
            {
                "id": r.id,
                "name": r.name,
                "address": r.user.address if r.user else None,
                "avatar": r.user.avatar if r.user else None,
                "cover_image": r.cover_image,
                "description": r.description,
                "cuisine_type": r.cuisine_type.value if r.cuisine_type else None,
                "opening_time": r.opening_time.strftime("%H:%M") if r.opening_time else None,
                "closing_time": r.closing_time.strftime("%H:%M") if r.closing_time else None
            }
            for r in restaurants_pagination.items
        ]

        dish_data = [
            {
                "id": d.id,
                "name": d.name,
                "description": d.description,
                "image": d.image,
                "price": d.price,
                "category": d.category.value if d.category else None,
                "restaurant_id": d.restaurant_id,
                "restaurant_name": d.restaurant.name if d.restaurant else None,
                "restaurant_avatar": d.restaurant.user.avatar if d.restaurant and d.restaurant.user else None
            }
            for d in dishes_pagination.items
        ]

        return jsonify({
            "data": restaurant_data,
            "dishes": dish_data,
            "keyword": keyword,
            "page": restaurants_pagination.page,
            "per_page": restaurants_pagination.per_page,
            "total": restaurants_pagination.total,
            "pages": restaurants_pagination.pages
        }), 200

    @staticmethod
    def search_web():
        if current_user.is_authenticated:
            if current_user.role == UserRole.ADMIN:
                return redirect('/admin/')
            elif current_user.role == UserRole.RESTAURANT:
                return redirect(url_for('me_bp.me_page'))

        keyword = request.args.get('q', '').strip()
        tab = request.args.get('tab', 'restaurants')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 9, type=int)

        if tab == 'dishes':
            dishes_pagination = RestaurantsDao.search_dishes(keyword, page, per_page)
            restaurants_pagination = RestaurantsDao.search_restaurants(keyword, 1, 9)
        else:
            restaurants_pagination = RestaurantsDao.search_restaurants(keyword, page, per_page)
            dishes_pagination = RestaurantsDao.search_dishes(keyword, 1, 9)

        return render_template(
            "searchCustomer.html",
            title="Tìm kiếm",
            restaurants_pagination=restaurants_pagination,
            dishes_pagination=dishes_pagination,
            keyword=keyword,
            current_tab=tab,
            page=page,
            per_page=per_page
        )