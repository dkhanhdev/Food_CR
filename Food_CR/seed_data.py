import json
import os
import random
import sys

# Ensure UTF-8 output encoding on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.models.model import (
    User, Restaurant, Dish, Voucher, Order, OrderItem,
    UserRole, CuisineType, DishCategory, DiscountType, Status,
    RestaurantApprovalStatus, SystemConfig,
    hash_password, parse_time, DEFAULT_MAX_CART_ITEMS
)
from sqlalchemy import text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESTAURANTS_JSON = os.path.join(BASE_DIR, "app", "data", "restaurants.json")
DISHES_JSON = os.path.join(BASE_DIR, "app", "data", "dishes.json")


def random_date_in_range(days=30):
    """Sinh thời điểm ngẫu nhiên trong khoảng từ `days` ngày trước đến hiện tại (UTC)."""
    now = datetime.utcnow()
    random_seconds = random.randint(0, int(days * 86400))
    return now - timedelta(seconds=random_seconds)


def seed(app=None):
    if app is None:
        app = create_app()
    with app.app_context():
        if db.engine.dialect.name == 'postgresql':
            with db.engine.connect() as conn:
                conn.execute(text("""
                    DO $$ DECLARE
                        r RECORD;
                    BEGIN
                        FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                            EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                        END LOOP;
                        FOR r IN (SELECT typname FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid GROUP BY typname) LOOP
                            EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
                        END LOOP;
                    END $$;
                """))
                conn.commit()
        elif db.engine.dialect.name == 'mysql':
            db.session.execute(text("SET FOREIGN_KEY_CHECKS=0"))
            db.session.commit()
            db.drop_all()
        else:
            db.drop_all()

        db.create_all()

        if User.query.first():
            print("ℹ Data already exists, skipping seed.")
            return

        # ---------- Admin & Customer mẫu ----------
        # Admin: username=admin, password=123456
        new_admin = User(
            name="Quản trị viên",
            username="admin",
            role = UserRole.ADMIN,
            password=hash_password("123456"),
            avatar="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTfjno7hGrNNuPZwaFZ8U8Mhr_Yq39rzd_p0YN_HVYk6KFmMETjtgd9bwl0UhU6g4xDDGg&usqp=CAU",
        )

        new_customer = User(
            name="Customer",
            username="customer",
            password=hash_password("customer"),
            avatar="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTfjno7hGrNNuPZwaFZ8U8Mhr_Yq39rzd_p0YN_HVYk6KFmMETjtgd9bwl0UhU6g4xDDGg&usqp=CAU",
            role=UserRole.CUSTOMER
        )

        db.session.add(SystemConfig(name='system', max_cart_items=DEFAULT_MAX_CART_ITEMS))
        db.session.add_all([new_admin, new_customer])
        db.session.commit()

        # ---------- Đọc dữ liệu nhà hàng từ JSON ----------
        with open(RESTAURANTS_JSON, "r", encoding="utf-8") as f:
            restaurants_data = json.load(f)

        restaurant_map = {}

        for r in restaurants_data:
            new_user = User(
                name=r["name"],
                username=r["username"],
                password=hash_password(r["password"]),
                phonenumber=r.get("phonenumber"),
                email=r.get("email"),
                address=r.get("address"),
                avatar=r.get("avatar"),
                role=UserRole.RESTAURANT
            )
            db.session.add(new_user)
            db.session.flush()

            new_restaurant = Restaurant(
                id=new_user.id,
                name=r["name"],
                cover_image=r.get("cover_image"),
                description=r.get("description"),
                status=r.get("status", True),
                opening_time=parse_time(r.get("opening_time")),
                closing_time=parse_time(r.get("closing_time")),
                cuisine_type=CuisineType[r["cuisine_type"]] if r.get("cuisine_type") else None,
                tax_code=r.get("tax_code"),
                approval_status=RestaurantApprovalStatus.APPROVED,
            )
            db.session.add(new_restaurant)
            restaurant_map[r["username"]] = new_restaurant

        db.session.commit()

        # ---------- Đọc dữ liệu món ăn từ JSON ----------
        with open(DISHES_JSON, "r", encoding="utf-8") as f:
            dishes_data = json.load(f)

        for d in dishes_data:
            restaurant_obj = restaurant_map.get(d["restaurant_username"])
            if not restaurant_obj:
                continue

            # Thêm 3 số 0 vào giá tiền món ăn (nhân 1000 sang VNĐ)
            raw_price = float(d.get("price", 0))
            price = raw_price * 1000 if raw_price < 1000 else raw_price

            new_dish = Dish(
                name=d["name"],
                description=d.get("description"),
                image=d.get("image"),
                price=price,
                category=DishCategory[d["category"]],
                restaurant=restaurant_obj
            )
            db.session.add(new_dish)

        db.session.commit()

        # ---------- 5 nhà hàng PENDING để test duyệt ----------
        pending_restaurants = [
            ("Bún Bò Huế Cô Ba", "bunbohue", "123456", "Huế", CuisineType.VIETNAMESE, "06:00", "22:00"),
            ("Lẩu Cua Đồng Út Tịch", "laucua", "123456", "Cần Thơ", CuisineType.VIETNAMESE, "10:00", "23:00"),
            ("Ốc Đào Cô Liên", "ocddao", "123456", "Sài Gòn", CuisineType.SEAFOOD, "11:00", "23:00"),
            ("Cháo Lòng Bà Điệp", "chaolong", "123456", "Hà Nội", CuisineType.VIETNAMESE, "06:00", "14:00"),
            ("Cơm Niêu Đệ Nhất", "comnieu", "123456", "Nha Trang", CuisineType.VIETNAMESE, "10:00", "21:00"),
        ]

        for name, username, pw, addr, ctype, open_t, close_t in pending_restaurants:
            new_user = User(
                name=name,
                username=username,
                password=hash_password(pw),
                email=f"{username}@email.com",
                address=addr,
                role=UserRole.RESTAURANT,
                active=False,
            )
            db.session.add(new_user)
            db.session.flush()

            new_restaurant = Restaurant(
                id=new_user.id,
                name=name,
                active=False,
                approval_status=RestaurantApprovalStatus.PENDING,
                cuisine_type=ctype,
                opening_time=parse_time(open_t),
                closing_time=parse_time(close_t),
            )
            db.session.add(new_restaurant)

        db.session.commit()
        print(f"✅ Thêm {len(pending_restaurants)} nhà hàng chờ duyệt.")

        _seed_orders(restaurant_map)
        _seed_orders_full_status(restaurant_map)

        print(f"✅ Đã tạo {len(restaurant_map)} nhà hàng và {len(dishes_data)} món ăn.")


def _seed_orders(restaurant_map):
    """Tạo đơn hàng test cho nhà hàng đã duyệt, trải đủ trạng thái, nhiều khách hàng khác nhau."""
    customer_specs = [
        ("Nguyen Van A", "khach_a", "0911000111", "khacha@example.com", "12 Le Loi, Q1, TP.HCM"),
        ("Tran Thi B", "khach_b", "0911000222", "khachb@example.com", "34 Nguyen Hue, Q3, TP.HCM"),
        ("Le Van C", "khach_c", "0911000333", "khachc@example.com", "56 Hai Ba Trung, Q7, TP.HCM"),
        ("Pham Thi D", "khach_d", "0911000444", "khachd@example.com", "78 Ly Thuong Kiet, Q10, TP.HCM"),
    ]

    customer_users = []
    for name, username, phone, email, addr in customer_specs:
        customer = User(
            name=name,
            username=username,
            password=hash_password("123456"),
            phonenumber=phone,
            email=email,
            address=addr,
            role=UserRole.CUSTOMER,
        )
        db.session.add(customer)
        customer_users.append(customer)
    db.session.flush()

    # Voucher mẫu cho nhà hàng test (quan_trua_ngon)
    rest_test = restaurant_map.get("quan_trua_ngon")
    vouchers = []
    if rest_test:
        vouchers = [
            Voucher(
                name="Giam 10% toi da 50k",
                code="QUANTRUANGON10",
                description="Giam 10% don hang, toi da 50k",
                discount_type=DiscountType.PERCENTAGE,
                discount_value=10,
                minimum_order=100000,
                max_discount=50000,
                start_date=datetime.utcnow() - timedelta(days=60),
                end_date=datetime.utcnow() + timedelta(days=60),
                usage_limit=1000,
                used_count=15,
                restaurant_id=rest_test.id,
            ),
            Voucher(
                name="Giam 30k",
                code="QUANTRUANGON30",
                description="Giam 30k don hang tu 150k",
                discount_type=DiscountType.FIXED_AMOUNT,
                discount_value=30000,
                minimum_order=150000,
                max_discount=None,
                start_date=datetime.utcnow() - timedelta(days=60),
                end_date=datetime.utcnow() + timedelta(days=60),
                usage_limit=1000,
                used_count=10,
                restaurant_id=rest_test.id,
            ),
        ]
        db.session.add_all(vouchers)
        db.session.flush()

    statuses_pool = [
        Status.COMPLETED, Status.COMPLETED, Status.COMPLETED, Status.COMPLETED,
        Status.COMPLETED, Status.COMPLETED, Status.PAID, Status.PAID,
        Status.PREPARING, Status.DELIVERING, Status.CONFIRMED, Status.CANCELLED
    ]
    notes_pool = [
        "Giao giờ hành chính", "Giao trưa 11h30", "Thêm ít tương ớt",
        "Để ở quầy lễ tân", "Gọi trước khi giao 5 phút", None, None, None
    ]
    rejection_reasons = [
        "Nhà hàng hết nguyên liệu", "Khách đổi ý hủy đơn", "Quá giờ giao hàng", "Không liên lạc được khách"
    ]

    orders_created = 0

    # 1. Tạo các đơn hàng mẫu theo cấu hình cụ thể với ngày random trong 30 ngày
    order_specs = [
        ("quan_trua_ngon", Status.PAID, 0, 20000, 0, "Giao gio hanh chinh"),
        ("quan_trua_ngon", Status.PAID, 1, 20000, 1, None),
        ("quan_trua_ngon", Status.PAID, 2, 15000, None, "Them it tuong ot"),
        ("quan_trua_ngon", Status.PAID, 3, 25000, 0, None),
        ("quan_trua_ngon", Status.CONFIRMED, 1, 20000, None, None),
        ("quan_trua_ngon", Status.CONFIRMED, 2, 15000, 1, "Giao trua 11h30"),
        ("quan_trua_ngon", Status.PREPARING, 0, 20000, None, None),
        ("quan_trua_ngon", Status.PREPARING, 3, 15000, 0, None),
        ("quan_trua_ngon", Status.DELIVERING, 2, 20000, None, None),
        ("quan_trua_ngon", Status.DELIVERING, 1, 25000, 1, None),
        ("quan_trua_ngon", Status.COMPLETED, 0, 20000, None, None),
        ("quan_trua_ngon", Status.CANCELLED, 3, 0, None, "Nha hang het nguyen lieu"),
        ("quan_trua_ngon", Status.PENDING_PAYMENT, 1, 20000, None, None),
        ("goc_trua_van_phong", Status.PAID, 2, 15000, None, None),
        ("goc_trua_van_phong", Status.CONFIRMED, 3, 20000, None, None),
        ("goc_trua_van_phong", Status.PREPARING, 0, 15000, None, None),
        ("goc_trua_van_phong", Status.DELIVERING, 1, 20000, None, None),
        ("goc_trua_van_phong", Status.COMPLETED, 2, 15000, None, None),
        ("goc_trua_van_phong", Status.CANCELLED, 3, 0, None, "Khach huy don"),
    ]

    for username, status, cust_idx, ship_fee, voucher_idx, note in order_specs:
        restaurant = restaurant_map.get(username)
        if not restaurant:
            continue
        customer = customer_users[cust_idx]
        dishes = Dish.query.filter_by(restaurant_id=restaurant.id).order_by(Dish.id).all()
        if not dishes:
            continue

        voucher = vouchers[voucher_idx] if (voucher_idx is not None and voucher_idx < len(vouchers)) else None
        chosen = dishes[:min(3, len(dishes))]
        items = []
        subtotal = 0
        for i, dish in enumerate(chosen):
            qty = (i % 3) + 1
            unit_price = float(dish.price)
            subtotal += unit_price * qty
            items.append(OrderItem(name=dish.name, dish_id=dish.id, unit_price=unit_price, quantity=qty))

        discount = 0
        if voucher:
            if voucher.discount_type == DiscountType.PERCENTAGE:
                discount = subtotal * voucher.discount_value / 100
                if voucher.max_discount is not None:
                    discount = min(discount, voucher.max_discount)
            else:
                discount = min(voucher.discount_value, subtotal)
        total = max(0, subtotal - discount + ship_fee)

        rejection_reason = note if status == Status.CANCELLED else None
        order = Order(
            name=f"DH-{orders_created + 1:05d}",
            user_id=customer.id,
            restaurant_id=restaurant.id,
            voucher_id=voucher.id if voucher else None,
            status=status,
            note=note,
            customer_name=customer.name,
            customer_phone=customer.phonenumber,
            customer_email=customer.email,
            delivery_address=customer.address,
            shipping_fee=ship_fee,
            total_amount=total,
            rejection_reason=rejection_reason,
            created_at=random_date_in_range(days=30),
        )
        order.items = items
        db.session.add(order)
        orders_created += 1

    # 2. Tạo thêm các đơn hàng ngẫu nhiên rải đều trong 30 ngày cho các nhà hàng để biểu đồ báo cáo đầy đủ
    for r_username, restaurant in restaurant_map.items():
        dishes = Dish.query.filter_by(restaurant_id=restaurant.id).all()
        if not dishes:
            continue
        # quan_trua_ngon tạo nhiều đơn hơn để xem dashboard báo cáo thật đẹp
        num_orders = random.randint(30, 45) if r_username == "quan_trua_ngon" else random.randint(4, 8)
        for _ in range(num_orders):
            customer = random.choice(customer_users)
            st = random.choice(statuses_pool)
            ship_fee = random.choice([15000, 20000, 25000, 30000])
            note = random.choice(notes_pool)
            rejection_reason = random.choice(rejection_reasons) if st == Status.CANCELLED else None

            sample_size = min(random.randint(1, 4), len(dishes))
            chosen_dishes = random.sample(dishes, sample_size)
            items = []
            subtotal = 0
            for dish in chosen_dishes:
                qty = random.randint(1, 3)
                unit_price = float(dish.price)
                subtotal += unit_price * qty
                items.append(OrderItem(name=dish.name, dish_id=dish.id, unit_price=unit_price, quantity=qty))

            voucher = None
            if vouchers and random.random() < 0.35 and r_username == "quan_trua_ngon":
                voucher = random.choice(vouchers)

            discount = 0
            if voucher:
                if voucher.discount_type == DiscountType.PERCENTAGE:
                    discount = subtotal * voucher.discount_value / 100
                    if voucher.max_discount is not None:
                        discount = min(discount, voucher.max_discount)
                else:
                    discount = min(voucher.discount_value, subtotal)
            total = max(0, subtotal - discount + ship_fee)

            order = Order(
                name=f"DH-{orders_created + 1:05d}",
                user_id=customer.id,
                restaurant_id=restaurant.id,
                voucher_id=voucher.id if voucher else None,
                status=st,
                note=note,
                customer_name=customer.name,
                customer_phone=customer.phonenumber,
                customer_email=customer.email,
                delivery_address=customer.address,
                shipping_fee=ship_fee,
                total_amount=total,
                rejection_reason=rejection_reason,
                created_at=random_date_in_range(days=30),
            )
            order.items = items
            db.session.add(order)
            orders_created += 1

    db.session.commit()
    print(f"✅ Đã tạo {orders_created} đơn hàng test rải đều trong 30 ngày.")


def _seed_orders_full_status(restaurant_map):
    """Tạo một khách test riêng và đủ 8 trạng thái Order."""

    test_customer = User(
        name="Nguyen Van Test",
        username="khach_test",
        password=hash_password("123456"),
        phonenumber="0900000000",
        email="khachtest@example.com",
        address="99 Vo Van Tan, Q3, TP.HCM",
        role=UserRole.CUSTOMER,
    )
    db.session.add(test_customer)
    db.session.flush()

    rest_test = restaurant_map.get("quan_trua_ngon")
    if not rest_test:
        return

    voucher = Voucher(
        name="Giam 10% toi da 50k",
        code="TESTVOUCHER10",
        description="Giam 10% don hang, toi da 50k",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=10,
        minimum_order=100000,
        max_discount=50000,
        start_date=datetime.utcnow() - timedelta(days=60),
        end_date=datetime.utcnow() + timedelta(days=60),
        usage_limit=1000,
        used_count=1,
        restaurant_id=rest_test.id,
    )
    db.session.add(voucher)
    db.session.flush()

    dishes = Dish.query.filter_by(restaurant_id=rest_test.id).order_by(Dish.id).all()
    if not dishes:
        print("⚠ Không có món ăn cho nhà hàng test, bỏ qua seed order đủ trạng thái.")
        return

    # spec: (status, ship_fee, dùng voucher?, note, rejection_reason)
    order_specs = [
        (Status.PENDING_PAYMENT, 20000, False, None, None),
        (Status.PAYMENT_FAILED, 20000, False, None, "Thanh toan that bai tu cong VNPAY"),
        (Status.PAID, 20000, True, "Giao gio hanh chinh", None),
        (Status.CONFIRMED, 15000, False, "Giao truoc 12h", None),
        (Status.PREPARING, 20000, True, None, None),
        (Status.DELIVERING, 25000, False, None, None),
        (Status.COMPLETED, 20000, True, None, None),
        (Status.CANCELLED, 0, False, "Khach doi y", "Khach huy don truoc khi xac nhan"),
    ]

    orders_created = 0
    for status, ship_fee, use_voucher, note, rejection_reason in order_specs:
        chosen = dishes[:min(3, len(dishes))]
        items = []
        subtotal = 0
        for i, dish in enumerate(chosen):
            qty = (i % 3) + 1
            unit_price = float(dish.price)
            subtotal += unit_price * qty
            items.append(OrderItem(name=dish.name, dish_id=dish.id, unit_price=unit_price, quantity=qty))

        discount = 0
        applied_voucher = voucher if use_voucher else None
        if applied_voucher:
            if applied_voucher.discount_type == DiscountType.PERCENTAGE:
                discount = subtotal * applied_voucher.discount_value / 100
                if applied_voucher.max_discount is not None:
                    discount = min(discount, applied_voucher.max_discount)
            else:
                discount = min(applied_voucher.discount_value, subtotal)

        total = max(0, subtotal - discount + ship_fee)

        order = Order(
            name=f"DH-TEST-{orders_created + 1:03d}",
            user_id=test_customer.id,
            restaurant_id=rest_test.id,
            voucher_id=applied_voucher.id if applied_voucher else None,
            status=status,
            note=note,
            customer_name=test_customer.name,
            customer_phone=test_customer.phonenumber,
            customer_email=test_customer.email,
            delivery_address=test_customer.address,
            shipping_fee=ship_fee,
            total_amount=total,
            rejection_reason=rejection_reason,
            created_at=random_date_in_range(days=30),
        )
        order.items = items
        db.session.add(order)

        orders_created += 1

    # Tạo thêm các đơn hàng của ngày hôm nay (today) chia đều 3 trạng thái pipeline (PAID, PREPARING, COMPLETED) cho quan_trua_ngon
    today_pipeline_statuses = [
        Status.PAID, Status.PAID, Status.PAID, Status.PAID,
        Status.PREPARING, Status.PREPARING, Status.PREPARING,
        Status.COMPLETED, Status.COMPLETED, Status.COMPLETED
    ]
    now = datetime.utcnow()
    for idx, st in enumerate(today_pipeline_statuses):
        sample_size = min(random.randint(1, 3), len(dishes))
        chosen = random.sample(dishes, sample_size)
        items = []
        subtotal = 0
        for i, dish in enumerate(chosen):
            qty = random.randint(1, 2)
            unit_price = float(dish.price)
            subtotal += unit_price * qty
            items.append(OrderItem(name=dish.name, dish_id=dish.id, unit_price=unit_price, quantity=qty))

        ship_fee = 20000
        total = subtotal + ship_fee

        # Rải rác trong các giờ của ngày hôm nay (từ vài phút trước đến vài tiếng trước)
        created_today = now - timedelta(minutes=random.randint(5, 480))

        order = Order(
            name=f"DH-TODAY-{idx + 1:03d}",
            user_id=test_customer.id,
            restaurant_id=rest_test.id,
            voucher_id=None,
            status=st,
            note="Đơn hôm nay",
            customer_name=test_customer.name,
            customer_phone=test_customer.phonenumber,
            customer_email=test_customer.email,
            delivery_address=test_customer.address,
            shipping_fee=ship_fee,
            total_amount=total,
            created_at=created_today,
        )
        order.items = items
        db.session.add(order)
        orders_created += 1

    db.session.commit()
    print(f"✅ Đã tạo user '{test_customer.username}' và {orders_created} đơn hàng (bao gồm 10 đơn hôm nay chia đều 3 trạng thái).")

    try:
        from app.service.recommendation_train import train_association_rules
        print("🤖 Đang huấn luyện luật kết hợp gợi ý món ăn (FP-Growth)...")
        train_association_rules(app=app)
        print("✅ Hoàn tất huấn luyện luật kết hợp!")
    except Exception as e:
        print(f"⚠️ Không thể huấn luyện luật kết hợp: {e}")


if __name__ == "__main__":
    seed()