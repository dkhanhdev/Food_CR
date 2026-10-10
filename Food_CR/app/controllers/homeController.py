from flask import render_template, abort, redirect, url_for
from flask_login import current_user, login_required
from app.models.model import UserRole, CuisineType


def index():
    if current_user.is_authenticated:
        if current_user.role == UserRole.ADMIN:
            return redirect('/admin/')
        elif current_user.role == UserRole.RESTAURANT:
            return redirect(url_for('me_bp.me_page'))
    return render_template('homePage.html', title='KHM Foodie', description='Welcome to KHM Foodie! Explore the best food in Cambodia.')

def login_page():
    if current_user.is_authenticated:
        if current_user.role == UserRole.ADMIN:
            return redirect('/admin/')
        elif current_user.role == UserRole.RESTAURANT:
            return redirect(url_for('me_bp.me_page'))
        return redirect(url_for('home_bp.index'))
    return render_template('loginPage.html')

def register_page():
    if current_user.is_authenticated:
        if current_user.role == UserRole.ADMIN:
            return redirect('/admin/')
        elif current_user.role == UserRole.RESTAURANT:
            return redirect(url_for('me_bp.me_page'))
        return redirect(url_for('home_bp.index'))
    return render_template('registerPage.html')

def register_page_restaurant():
    if current_user.is_authenticated:
        if current_user.role == UserRole.RESTAURANT:
            return redirect(url_for('me_bp.me_page'))
        elif current_user.role == UserRole.ADMIN:
            return redirect('/admin/')
        return redirect(url_for('home_bp.index'))
    return render_template('registerPageRestaurant.html')

def me_page():
    role = current_user.role

    if role == UserRole.RESTAURANT:
        layout_template = 'layout/baseRestaurent.html'
        cuisine_types = [(c.name, c.value) for c in CuisineType]
        r = current_user.restaurant
        from app.dao.systemConfigDao import SystemConfigDao
        return render_template(
            'mePage.html',
            layout_template=layout_template,
            role='Restaurant',
            cuisine_types=cuisine_types,
            opening_time=r.opening_time.strftime('%H:%M') if r and r.opening_time else '06:30',
            closing_time=r.closing_time.strftime('%H:%M') if r and r.closing_time else '22:30',
            is_open=r.status if r and r.status is not None else True,
            system_max_cart_items=SystemConfigDao.get_max_cart_items(None),
            restaurant_max_cart_items=SystemConfigDao.get_max_cart_items(current_user.id)
        )

    elif role == UserRole.CUSTOMER:
        layout_template = 'layout/baseCustomer.html'
        return render_template(
            'mePage.html',
            layout_template=layout_template,
            role='Customer'
        )

    else:
        layout_template = 'layout/baseCustomer.html'
        return render_template(
            'mePage.html',
            layout_template=layout_template,
            role='Guest'
        )


@login_required
def promotions_page():
    role = current_user.role
    if role != UserRole.RESTAURANT:
        abort(403)

    return render_template(
        'promotionsPage.html',
        title='Khuyến mãi'
    )


@login_required
def order_detail_page(restaurant_id):
    if current_user.role == UserRole.ADMIN:
        return redirect('/admin/')
    elif current_user.role == UserRole.RESTAURANT:
        return redirect(url_for('me_bp.me_page'))
    return render_template('orderDetail.html', restaurant_id=restaurant_id)


@login_required
def payment_countdown_page(order_id):
    if current_user.role == UserRole.ADMIN:
        return redirect('/admin/')
    elif current_user.role == UserRole.RESTAURANT:
        return redirect(url_for('me_bp.me_page'))
    return render_template('paymentCountdown.html', order_id=order_id)
