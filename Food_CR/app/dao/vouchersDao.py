from sqlalchemy import or_

from app.extensions import db
from app.models.model import Voucher, VoucherDish


class VouchersDao:
    @staticmethod
    def get_order_voucher_by_code(code, restaurant_id):
        """Trả về Voucher đơn hàng (không gắn dish) khớp code, active, thuộc nhà hàng này."""
        return Voucher.query.filter(
            Voucher.code == code,
            Voucher.active == True,
            or_(Voucher.restaurant_id == restaurant_id, Voucher.restaurant_id.is_(None)),
            ~Voucher.dish_links.any()
        ).first()

    @staticmethod
    def get_by_code_any_status(code):
        """Trả về Voucher khớp code bất kể active hay không (dùng để phát hiện mã đã bị xoá mềm)."""
        return Voucher.query.filter(Voucher.code == code).first()

    @staticmethod
    def get_public_order_vouchers(restaurant_id):
        """Voucher loại ORDER (không gắn món), đang active, thuộc nhà hàng này - để hiển thị công khai cho khách."""
        vouchers = Voucher.query.filter(
            Voucher.restaurant_id == restaurant_id,
            Voucher.active == True,
            ~Voucher.dish_links.any()
        ).order_by(Voucher.end_date.asc()).all()
        return [v for v in vouchers if v.is_valid_now()]

    @staticmethod
    def get_all_by_restaurant(restaurant_id):
        return Voucher.query.filter_by(
            restaurant_id=restaurant_id,
            active=True
        ).order_by(Voucher.created_at.desc()).all()

    @staticmethod
    def get_by_id_and_restaurant(voucher_id, restaurant_id):
        return Voucher.query.filter_by(
            id=voucher_id,
            restaurant_id=restaurant_id,
            active=True
        ).first()

    @staticmethod
    def get_dish_conflicts(dish_ids, restaurant_id, exclude_voucher_id=None):
        """Trả về {dish_id: voucher} cho các món đã thuộc một voucher khác đang hiệu lực."""
        if not dish_ids:
            return {}

        query = VoucherDish.query.join(Voucher).filter(
            VoucherDish.dish_id.in_(dish_ids),
            Voucher.restaurant_id == restaurant_id,
        )
        if exclude_voucher_id is not None:
            query = query.filter(Voucher.id != exclude_voucher_id)

        conflicts = {}
        for link in query.all():
            if link.voucher.is_valid_now():
                conflicts[link.dish_id] = link.voucher
        return conflicts

    @staticmethod
    def create_voucher(voucher, dishes):
        db.session.add(voucher)
        db.session.flush()
        VouchersDao.replace_dishes(voucher, dishes)
        db.session.commit()
        return voucher

    @staticmethod
    def save(voucher):
        db.session.commit()
        return voucher

    @staticmethod
    def replace_dishes(voucher, dishes):
        voucher.dish_links = [
            VoucherDish(voucher=voucher, dish=dish)
            for dish in dishes
        ]

    @staticmethod
    def soft_delete(voucher):
        voucher.active = False
        db.session.commit()
        return voucher
