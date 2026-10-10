import hashlib
from datetime import datetime, time as dtime
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean,
    Float, Enum, ForeignKey, Time, UniqueConstraint, Text, Numeric
)
from sqlalchemy.orm import relationship, backref
from flask_login import UserMixin
from enum import Enum as RoleEnum
from app.extensions import db

DEFAULT_MAX_CART_ITEMS = 20


class Base(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active = Column(Boolean, default=True)

    def __str__(self):
        return self.name


class UserRole(RoleEnum):
    ADMIN = "Admin"
    CUSTOMER = "Customer"
    RESTAURANT = "Restaurant"


class User(Base, UserMixin):
    __tablename__ = 'user'
    username = Column(String(150), unique=True, nullable=True)
    password = Column(String(150), nullable=True)
    phonenumber = Column(String(150), nullable=True)
    avatar = Column(String(300), default="https://res.cloudinary.com/dy1unykph/image/upload/v1740037805/apple-iphone-16-pro-natural-titanium_lcnlu2.webp")
    email = Column(String(150), unique=True, nullable=True)
    address = Column(String(300), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER)
    auth_provider = Column(String(50), default='local')
    restaurant = relationship(
        'Restaurant',
        backref=backref('user', uselist=False),
        uselist=False
    )
    carts = relationship('Cart', backref='user', lazy=True)


class CuisineType(RoleEnum):
    VIETNAMESE = "Món Việt"
    ASIAN = "Món Á"
    WESTERN = "Món Âu"
    JAPANESE = "Món Nhật"
    KOREAN = "Món Hàn"
    CHINESE = "Món Trung"
    THAI = "Món Thái"
    VEGETARIAN = "Món chay"
    FAST_FOOD = "Đồ ăn nhanh"
    SEAFOOD = "Hải sản"
    BBQ_HOTPOT = "Nướng & Lẩu"
    CAFE_DESSERT = "Cafe & Tráng miệng"
    OTHER = "Khác"

class RestaurantApprovalStatus(RoleEnum):
    PENDING = "Chờ duyệt"
    APPROVED = "Đã duyệt"
    REJECTED = "Bị từ chối"

class Restaurant(Base):
    __tablename__ = 'restaurant'
    id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    description = Column(String(500), nullable=True)
    rejection_reason = Column(String(500), nullable=True)
    status = Column(Boolean, default=True)
    opening_time = Column(Time, nullable=True)
    closing_time = Column(Time, nullable=True)
    cuisine_type = Column(Enum(CuisineType), nullable=True)
    tax_code = Column(String(50), nullable=True)
    cover_image = Column(String(300), nullable=True)
    approval_status = Column(Enum(RestaurantApprovalStatus), default=RestaurantApprovalStatus.PENDING)

    carts = relationship('Cart', backref='restaurant', lazy=True)
    vouchers = relationship('Voucher', backref='restaurant', lazy=True)


class DishCategory(RoleEnum):
    APPETIZER = "Món khai vị"
    MAIN_COURSE = "Món chính"
    DESSERT = "Món tráng miệng"
    BEVERAGE = "Đồ uống"
    SIDE_DISH = "Món ăn kèm"


class DiscountType(RoleEnum):
    PERCENTAGE = "Phần trăm"
    FIXED_AMOUNT = "Số tiền cố định"

class Status(RoleEnum):
    PENDING_PAYMENT = "Pending Payment"
    PAYMENT_FAILED = "Payment Failed"
    PAID = "Paid"
    CONFIRMED = "Confirmed"
    PREPARING = "Preparing"
    DELIVERING = "Delivering"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class OrderStatus(RoleEnum):
    PENDING_PAYMENT = "Pending Payment"
    PAYMENT_FAILED = "Payment Failed"
    PAID = "Paid"
    CONFIRMED = "Confirmed"
    PREPARING = "Preparing"
    DELIVERING = "Delivering"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class Dish(Base):
    __tablename__ = 'dish'
    description = Column(String(500), nullable=True)
    image = Column(String(300), nullable=True)
    price = Column(Float, nullable=False)
    category = Column(Enum(DishCategory), nullable=False)
    restaurant_id = Column(Integer, ForeignKey('restaurant.id'), nullable=False)
    restaurant = relationship('Restaurant', backref=backref('dishes', lazy=True))
    voucher_links = relationship(
        'VoucherDish',
        back_populates='dish',
        cascade='all, delete-orphan',
        lazy=True
    )

    def get_active_voucher(self):
        for link in self.voucher_links:
            if link.voucher and link.voucher.is_valid_now():
                return link.voucher
        return None

class Cart(Base):
    __tablename__ = 'cart'
    __table_args__ = (
        UniqueConstraint('user_id', 'restaurant_id', name='uq_cart_user_restaurant'),
    )
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    restaurant_id = Column(Integer, ForeignKey('restaurant.id'), nullable=False)
    note = Column(String(300), nullable=True)

class Voucher(Base):
    __tablename__ = 'voucher'
    code = Column(String(50), unique=True, nullable=False)
    description = Column(String(500), nullable=True)
    discount_type = Column(Enum(DiscountType), nullable=False)
    discount_value = Column(Float, nullable=False)
    minimum_order = Column(Float, default=0)
    max_discount = Column(Float, nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    usage_limit = Column(Integer, default=1)
    used_count = Column(Integer, default=0)
    restaurant_id = Column(Integer, ForeignKey('restaurant.id'), nullable=True)
    dish_links = relationship(
        'VoucherDish',
        back_populates='voucher',
        cascade='all, delete-orphan',
        lazy=True
    )

    def is_valid_now(self, now=None):
        now = now or datetime.utcnow()
        if not self.active:
            return False
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False
        return True

    def apply_discount(self, price):
        if self.discount_type == DiscountType.PERCENTAGE:
            discount = price * (self.discount_value / 100)
            if self.max_discount:
                discount = min(discount, self.max_discount)
        else:
            discount = self.discount_value

        discount = max(0, min(discount, price))
        return round(price - discount, 2)

class VoucherDish(db.Model):
    __tablename__ = 'voucher_dish'

    voucher_id = Column(
        Integer,
        ForeignKey('voucher.id', ondelete='CASCADE'),
        primary_key=True
    )
    dish_id = Column(
        Integer,
        ForeignKey('dish.id', ondelete='CASCADE'),
        primary_key=True
    )
    voucher = relationship('Voucher', back_populates='dish_links')
    dish = relationship('Dish', back_populates='voucher_links')

class CartItems(Base):
    __tablename__ = 'cart_items'
    __table_args__ = (
        UniqueConstraint('cart_id', 'dish_id', name='uq_cart_items_cart_dish'),
    )
    cart_id = Column(Integer, ForeignKey('cart.id'), nullable=False)
    dish_id = Column(Integer, ForeignKey('dish.id'), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    price = Column(Float, nullable=False)
    cart = relationship('Cart', backref=backref('items', lazy=True))
    dish = relationship('Dish', backref=backref('cart_items', lazy=True))

    def __str__(self):
        return f"CartItem({self.cart_id}, {self.dish_id})"


class Order(Base):
    __tablename__ = 'orders'

    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    restaurant_id = Column(Integer, ForeignKey('restaurant.id'), nullable=False)
    voucher_id = Column(Integer, ForeignKey('voucher.id'), nullable=True)

    status = Column(Enum(Status), default=Status.PENDING_PAYMENT, nullable=False)
    note = Column(String(300), nullable=True)
    rejection_reason = Column(String(500), nullable=True)

    customer_name = Column(String(150), nullable=False)
    customer_phone = Column(String(50), nullable=True)
    customer_email = Column(String(150), nullable=True)
    delivery_address = Column(String(300), nullable=True)

    shipping_fee = Column(Numeric(12, 0), nullable=False, default=0)
    discount_amount = Column(Numeric(12, 0), nullable=False, default=0)
    total_amount = Column(Numeric(12, 0), nullable=False, default=0)
    payment_deadline = Column(DateTime, nullable=True)

    # MoMo payment tracking (thay cho bảng PaymentTransaction riêng)
    momo_order_id = Column(String(100), unique=True, nullable=True)
    momo_request_id = Column(String(100), nullable=True)
    paid_by = Column(String(150), nullable=True, default="")

    user = relationship('User', backref=backref('orders', lazy=True))
    restaurant = relationship('Restaurant', backref=backref('orders', lazy=True))
    voucher = relationship('Voucher', backref=backref('orders', lazy=True))
    items = relationship(
        'OrderItem',
        backref='order',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def __str__(self):
        return f"Order({self.id}, {self.status.value})"

class OrderItem(Base):
    __tablename__ = 'order_items'

    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    dish_id = Column(Integer, ForeignKey('dish.id'), nullable=False)

    unit_price = Column(Numeric(12, 0), nullable=False)
    quantity = Column(Integer, nullable=False)

    dish = relationship('Dish', backref=backref('order_items', lazy=True))

    def __str__(self):
        return f"OrderItem({self.order_id}, {self.dish_id})"



class SystemConfig(Base):
    __tablename__ = 'system_config'
    max_cart_items = Column(Integer, default=DEFAULT_MAX_CART_ITEMS, nullable=False)


class RestaurantConfig(Base):
    """Cấu hình riêng của từng nhà hàng; tồn tại row = override, không có row = dùng giá trị admin."""
    __tablename__ = 'restaurant_config'
    name = Column(String(150), nullable=False, default=lambda: "restaurant-config")
    restaurant_id = Column(Integer, ForeignKey('restaurant.id'), unique=True, nullable=False)
    max_cart_items = Column(Integer, nullable=False)
    restaurant = relationship('Restaurant')


class Review(Base):
    __tablename__ = 'review'
    __table_args__ = (
        UniqueConstraint('user_id', 'restaurant_id', name='uq_review_user_restaurant'),
    )
    
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    restaurant_id = Column(Integer, ForeignKey('restaurant.id'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=True)

    # Override Base.name: a review has no name of its own
    name = Column(String(150), nullable=True)

    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(String(1000), nullable=True)
    
    # Timestamps inherited from Base: created_at, created_updated_at, active
    user = relationship('User', backref='reviews', lazy=True)
    restaurant = relationship('Restaurant', backref='reviews', lazy=True)
    order = relationship('Order', backref='review', uselist=False, lazy=True)
    images = relationship('ReviewImage', backref='review', lazy=True, cascade='all, delete-orphan')

    def __str__(self):
        return f"Review({self.id}, rating={self.rating}, user_id={self.user_id})"


class ReviewImage(db.Model):
    __tablename__ = 'review_image'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(Integer, ForeignKey('review.id', ondelete='CASCADE'), nullable=False)
    image_url = Column(String(300), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    def __str__(self):
        return f"ReviewImage({self.id}, review_id={self.review_id})"


class AssociationRule(db.Model):
    __tablename__ = 'association_rules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(Integer, ForeignKey('restaurant.id'), nullable=True)
    antecedent_dish_id = Column(Integer, ForeignKey('dish.id'), nullable=False)
    consequent_dish_id = Column(Integer, ForeignKey('dish.id'), nullable=False)

    support = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    lift = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    restaurant = relationship('Restaurant', backref=backref('association_rules', lazy=True))
    antecedent_dish = relationship('Dish', foreign_keys=[antecedent_dish_id], backref=backref('antecedent_rules', lazy=True))
    consequent_dish = relationship('Dish', foreign_keys=[consequent_dish_id], backref=backref('consequent_rules', lazy=True))

    def __str__(self):
        return f"AssociationRule({self.antecedent_dish_id} -> {self.consequent_dish_id}, lift={self.lift:.2f})"


def hash_password(raw_password: str) -> str:
    return str(hashlib.md5(raw_password.encode('utf-8')).hexdigest())


def parse_time(time_str):
    if not time_str:
        return None
    h, m = map(int, time_str.split(':'))
    if h == 24:
        h = 23
        m = 59
    return dtime(hour=h, minute=m)
