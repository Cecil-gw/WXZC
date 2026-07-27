import pandas as pd
import numpy as np

def clean_iot_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    def time_process(df_in):
        df_in["timestamp"] = pd.to_datetime(df_in["timestamp"], errors="coerce")
        df_in = df_in.dropna(subset=["timestamp"])
        df_in = df_in.sort_values(by=["sensor_id", "timestamp"])
        df_in = df_in.drop_duplicates(subset=["sensor_id", "timestamp"], keep="first")
        return df_in

    def value_clean(df_in):
        df_in["temperature"] = df_in["temperature"].mask(
            (df_in["temperature"] < -10) | (df_in["temperature"] > 50)
        )
        df_in["battery"] = df_in["battery"].mask(
            (df_in["battery"] < 0) | (df_in["battery"] > 100)
        )
        mask_offline = df_in["status"] == "offline"
        df_in.loc[mask_offline, ["temperature", "humidity"]] = np.nan
        return df_in

    # 分组线性插值
    def interp_group(group):
        group[["temperature", "humidity"]] = group[["temperature", "humidity"]].interpolate(method="linear")
        group[["temperature", "humidity"]] = group[["temperature", "humidity"]].ffill().bfill()
        return group

    df = time_process(df)
    df = value_clean(df)
    df = df.groupby("sensor_id", group_keys=False).apply(interp_group)
    df = df.reset_index(drop=True)
    return df


# ===================== 使用部分 =====================
if __name__ == "__main__":
    raw_df = pd.read_csv(R'D:\wx26.7.14\7.27\iot_sensor_dirty.csv')
    
    clean_df = clean_iot_data(raw_df)

    clean_df.to_csv(R'D:\wx26.7.14\7.27\sensor_clean.csv', index=False, encoding="utf-8-sig")

    print("清洗完成！")
    print("原始行数：", len(raw_df))
    print("清洗后行数：", len(clean_df))