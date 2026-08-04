import io
from typing import Any, Dict, List, Optional

from app.core.security import create_access_token, hash_password
from app.models.customer import Customer
from app.models.user import User


def create_token(user_id: int, role: str, username: Optional[str] = None) -> str:
    return create_access_token(user_id, role, username)


def create_admin(db) -> Dict[str, Any]:
    admin = User(
        username="test_admin",
        password_hash=hash_password("admin123"),
        role="admin",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return {
        "id": admin.id,
        "username": admin.username,
        "role": admin.role,
    }


def create_regular_user(db) -> Dict[str, Any]:
    user = User(
        username="test_user",
        password_hash=hash_password("user123"),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
    }


def admin_headers(user_id: int, username: str) -> Dict[str, str]:
    token = create_token(user_id, "admin", username)
    return {"Authorization": f"Bearer {token}"}


def user_headers(user_id: int, username: str) -> Dict[str, str]:
    token = create_token(user_id, "user", username)
    return {"Authorization": f"Bearer {token}"}


def _generate_customer_rows(n: int = 30, response_1_ratio: float = 0.3) -> List[Dict[str, Any]]:
    rows = []
    for i in range(1, n + 1):
        gender = "Male" if i % 2 == 0 else "Female"
        age = 20 + (i % 50)
        driving_license = 1 if i % 3 != 0 else 0
        region_code = float((i % 100) + 1)
        previously_insured = 1 if i % 4 == 0 else 0
        vehicle_age = ["< 1 Year", "1-2 Year", "> 2 Years"][i % 3]
        vehicle_damage = "Yes" if i % 5 == 0 else "No"
        annual_premium = 2000.0 + (i * 50)
        policy_sales_channel = float((i % 10) + 1)
        vintage = 100 + (i % 200)
        response = 1 if i < int(n * response_1_ratio) else 0
        rows.append({
            "id": i,
            "Gender": gender,
            "Age": age,
            "Driving_License": driving_license,
            "Region_Code": region_code,
            "Previously_Insured": previously_insured,
            "Vehicle_Age": vehicle_age,
            "Vehicle_Damage": vehicle_damage,
            "Annual_Premium": annual_premium,
            "Policy_Sales_Channel": policy_sales_channel,
            "Vintage": vintage,
            "Response": response,
        })
    return rows


def upload_excel(client, headers: Dict[str, str], n: int = 30, filename: str = "test.xlsx"):
    data = _generate_customer_rows(n)
    import pandas as pd

    df = pd.DataFrame(data)
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)

    data_dict = {
        "file": (buf, filename),
    }
    return client.post(
        "/api/v1/data/upload",
        headers=headers,
        data=data_dict,
        content_type="multipart/form-data",
    )


def seed_customers(db, n: int = 30) -> List[Customer]:
    data = _generate_customer_rows(n)
    from app.utils.data_processor import COLUMN_RENAME, validate_rows

    import pandas as pd
    df = pd.DataFrame(data)
    validation = validate_rows(df)
    rows = validation["rows"]
    from app.services.data_service import bulk_insert
    imported = bulk_insert(db, rows)
    return db.query(Customer).order_by(Customer.id).all()
