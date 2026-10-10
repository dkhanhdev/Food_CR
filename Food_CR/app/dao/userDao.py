from app.models.model import User, Restaurant, UserRole, CuisineType, hash_password
from app.extensions import db
import hashlib

class UserDao:

    @staticmethod
    def get_by_username(username):
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def check_userActive(user):
        user = User.query.get(user.id)
        if user:
            return user.active
        return None

    @staticmethod
    def get_by_id(user_id):
        return User.query.get(int(user_id))

    @staticmethod
    def get_admin_users():
        return User.query.filter_by(role=UserRole.ADMIN, active=True).all()

    @staticmethod
    def update_profile(user_id, data):
        user = User.query.get(int(user_id))
        if not user:
            return None

        # Base User fields (shared by Restaurant)
        for field in ['name', 'phonenumber', 'email', 'address', 'avatar']:
            if field in data and data[field] is not None:
                setattr(user, field, data[field])

        # Restaurant-specific fields
        if user.role == UserRole.RESTAURANT:
            restaurant = Restaurant.query.get(int(user_id))
            if restaurant:
                for field in ['description', 'cover_image', 'opening_time', 'closing_time', 'tax_code', 'status']:
                    if field in data and data[field] is not None:
                        setattr(restaurant, field, data[field])
                if 'cuisine_type' in data and data['cuisine_type'] is not None:
                    try:
                        restaurant.cuisine_type = CuisineType[data['cuisine_type']]
                    except (KeyError, ValueError):
                        pass

        db.session.commit()
        return user

def add_user(
    name,
    phonenumber=None,
    username=None,
    password=None,
    email=None,
    role=None,
    is_restaurant=False,
    **kwargs
):
    if password:
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

    common_data = dict(
        name=name.strip() if name else None,
        phonenumber=phonenumber.strip() if phonenumber else None,
        username=username.strip() if username else None,
        password=password if password else None,
        email=email.strip() if email else None,
        address=kwargs.get('address'),
        avatar=kwargs.get('avatar'),
        auth_provider=kwargs.get('auth_provider', 'local'),
    )
    if role:
        common_data['role'] = role

    if is_restaurant:
        common_data['active'] = False
        user = User(**common_data)
        db.session.add(user)
        db.session.flush()

        restaurant = Restaurant(
            id=user.id,
            name=common_data['name'],
            description=kwargs.get('description'),
            opening_time=kwargs.get('opening_time'),
            closing_time=kwargs.get('closing_time'),
            cuisine_type=kwargs.get('cuisine_type'),
            tax_code=kwargs.get('tax_code'),
            cover_image=kwargs.get('cover_image'),
            active=False
        )
        db.session.add(restaurant)
    else:
        user = User(**common_data)
        db.session.add(user)

    db.session.commit()
    return user


def check_userEmail(email):
    return User.query.filter_by(email=email.strip().lower()).first()
