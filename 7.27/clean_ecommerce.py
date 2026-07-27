import pandas as pd
import numpy as np
import datetime as dt


def clean_ecommerce_log(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1. event_type标准化
    def normalize_event(event):
        if pd.isna(event):
            return "view"
        e = str(event).strip().lower()
        mapping = {
            "view": "view",
            "cart": "cart",
            "purchase": "purchase",
            "购买": "purchase"
        }
        return mapping.get(e, "view")

    df["event_type"] = df["event_type"].apply(normalize_event)

    # 2. 年龄过滤
    df = df[(df["user_age"] >= 0) & (df["user_age"] <= 100)]

    # 3. 时间解析，剔除无效时间
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])

    # 4. 去重，保留最新记录
    df = df.sort_values(["user_id", "item_id", "event_type", "timestamp"])
    df = df.drop_duplicates(
        subset=["user_id", "item_id", "event_type"],
        keep="last"
    )

    # 5. price分组中位数填充
    global_median_price = df["price"].median()

    def fill_price_by_category(group):
        med = group["price"].median()
        if pd.isna(med):
            return group["price"].fillna(global_median_price)
        return group["price"].fillna(med)

    df["price"] = df.groupby("category", group_keys=False).apply(fill_price_by_category)

    # 6. device清洗
    df["device"] = df["device"].astype(str).str.strip().str.lower()

    df = df.reset_index(drop=True)
    return df


if __name__ == "__main__":
    df_raw = pd.read_csv(R'D:\wx26.7.14\7.27\ecommerce_dirty.csv', encoding='utf-8')
    df_result = clean_ecommerce_log(df_raw)

    save_target = R'D:\wx26.+++++++++.14\7.27\ecommerce_clean.csv'
    df_result.to_csv(save_target, index=False, encoding="utf-8-sig")

    print("✅ 数据清洗完毕")
    print(f"源文件行数：{len(df_raw)}")
    print(f"清洗后行数：{len(df_result)}")
    print(f"保存路径：{save_target}")