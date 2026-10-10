import json
import logging
import os
import sys

# Ensure UTF-8 output encoding on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Ensure project root is on sys.path if run directly as a script
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
from typing import Dict, List, Optional, Tuple
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth, association_rules

from app.extensions import db
from app.models.model import User, Restaurant, Dish, AssociationRule

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_SAMPLE_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'data',
    'sample_transactions.json'
)


def train_restaurant_rules(
    restaurant: Restaurant,
    raw_transactions: List[List[str]],
    min_support: float = 0.1,
    min_confidence: float = 0.3,
    min_lift: float = 1.0
) -> List[AssociationRule]:
    """
    Chạy thuật toán FP-Growth và sinh luật kết hợp cho một nhà hàng cụ thể.
    Lưu kết quả trực tiếp vào bảng AssociationRule trong database.
    """
    dish_map: Dict[str, Dish] = {dish.name: dish for dish in restaurant.dishes}
    dish_id_map: Dict[int, str] = {dish.id: dish.name for dish in restaurant.dishes}

    # Ánh xạ tên món sang dish_id
    encoded_transactions: List[List[int]] = []
    for tx in raw_transactions:
        dish_ids = [dish_map[name].id for name in tx if name in dish_map]
        # Giữ lại các giao dịch có ít nhất 2 món hợp lệ
        if len(dish_ids) >= 2:
            encoded_transactions.append(dish_ids)

    if len(encoded_transactions) < 2:
        logger.warning(
            f"Nhà hàng '{restaurant.name}' (ID: {restaurant.id}) không đủ giao dịch hợp lệ để train (cần >= 2, có: {len(encoded_transactions)})."
        )
        return []

    # One-hot encoding với TransactionEncoder
    te = TransactionEncoder()
    te_ary = te.fit(encoded_transactions).transform(encoded_transactions)
    df = pd.DataFrame(te_ary, columns=te.columns_)

    # FP-Growth Frequent Itemsets
    frequent_itemsets = fpgrowth(df, min_support=min_support, use_colnames=True)
    if frequent_itemsets.empty:
        logger.info(f"Nhà hàng '{restaurant.name}' (ID: {restaurant.id}): Không tìm thấy frequent itemset với min_support={min_support}.")
        return []

    # Trích xuất luật kết hợp
    rules = association_rules(frequent_itemsets, metric='confidence', min_threshold=min_confidence)
    if rules.empty:
        logger.info(f"Nhà hàng '{restaurant.name}' (ID: {restaurant.id}): Không có luật thỏa mãn min_confidence={min_confidence}.")
        return []

    # Lọc luật: 1-to-1 antecedent -> consequent, lift >= min_lift
    filtered_rules = rules[
        (rules['lift'] >= min_lift) &
        (rules['antecedents'].apply(len) == 1) &
        (rules['consequents'].apply(len) == 1)
    ]

    if filtered_rules.empty:
        logger.info(f"Nhà hàng '{restaurant.name}' (ID: {restaurant.id}): Không có luật 1-1 nào đạt min_lift={min_lift}.")
        return []

    # Xóa các luật cũ của nhà hàng để đảm bảo tính idempotent
    AssociationRule.query.filter_by(restaurant_id=restaurant.id).delete()

    created_rules: List[AssociationRule] = []
    seen_pairs = set()

    for _, row in filtered_rules.iterrows():
        ant_id = int(list(row['antecedents'])[0])
        con_id = int(list(row['consequents'])[0])
        pair_key = (ant_id, con_id)

        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)

        support_val = float(row['support'])
        confidence_val = float(row['confidence'])
        lift_val = float(row['lift'])

        new_rule = AssociationRule(
            restaurant_id=restaurant.id,
            antecedent_dish_id=ant_id,
            consequent_dish_id=con_id,
            support=support_val,
            confidence=confidence_val,
            lift=lift_val
        )
        db.session.add(new_rule)
        created_rules.append(new_rule)

        ant_name = dish_id_map.get(ant_id, f"Dish#{ant_id}")
        con_name = dish_id_map.get(con_id, f"Dish#{con_id}")
        logger.info(
            f"  [Rule] {restaurant.name} | '{ant_name}' -> '{con_name}' "
            f"(Support: {support_val:.2f}, Conf: {confidence_val:.2f}, Lift: {lift_val:.2f})"
        )

    db.session.commit()
    logger.info(f"Đã lưu {len(created_rules)} luật kết hợp cho nhà hàng '{restaurant.name}' (ID: {restaurant.id}).")
    return created_rules


def train_association_rules(
    app=None,
    data_file_path: Optional[str] = None,
    min_support: float = 0.1,
    min_confidence: float = 0.3,
    min_lift: float = 1.0
) -> Dict[str, int]:
    """
    Đọc dữ liệu từ file sample_transactions.json, huấn luyện FP-Growth cho toàn bộ nhà hàng và lưu vào DB.
    """
    file_path = data_file_path or DEFAULT_SAMPLE_DATA_PATH

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy file giao dịch mẫu tại: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    def _execute():
        logger.info(f"Bắt đầu huấn luyện FP-Growth từ: {file_path}")
        results: Dict[str, int] = {}
        total_rules = 0

        for username, raw_transactions in data.items():
            user = User.query.filter_by(username=username).first()
            if not user or not user.restaurant:
                logger.warning(f"Không tìm thấy nhà hàng tương ứng với username '{username}', bỏ qua.")
                continue

            restaurant = user.restaurant
            logger.info(f"--- Đang xử lý: {restaurant.name} ({username}) ---")

            rules = train_restaurant_rules(
                restaurant=restaurant,
                raw_transactions=raw_transactions,
                min_support=min_support,
                min_confidence=min_confidence,
                min_lift=min_lift
            )
            results[username] = len(rules)
            total_rules += len(rules)

        logger.info(f"=== Huấn luyện hoàn tất! Tổng cộng {total_rules} luật kết hợp đã được lưu vào database. ===")
        return results

    if app is not None:
        with app.app_context():
            return _execute()
    else:
        return _execute()


if __name__ == '__main__':
    from app import create_app
    app_instance = create_app()
    with app_instance.app_context():
        train_association_rules(min_support=0.1, min_confidence=0.3, min_lift=1.0)
