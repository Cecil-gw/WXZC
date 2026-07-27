import pandas as pd
from pandas.api.types import is_numeric_dtype
import numpy as np

class AutoDataCleaner:
    def __init__(self, df: pd.DataFrame, col_missing_drop_threshold: float=0.5, iqr_scale: float=1.5):
        self.df = df.copy()
        self.col_missing_drop_threshold = col_missing_drop_threshold
        self.iqr_scale = iqr_scale

    def handle_missing_value(self):
        drop_cols = []
        deal_method = {}

        for col in self.df.columns:
            null_cnt = self.df[col].isna().sum()
            missing_rate = null_cnt / len(self.df)

            if missing_rate > self.col_missing_drop_threshold:
                drop_cols.append(col)
                deal_method[col] = "缺失率超过阈值，删除整列"
            else:
                if is_numeric_dtype(self.df[col]):
                    med = self.df[col].median()
                    self.df[col] = self.df[col].fillna(med)
                    deal_method[col] = "数值列，中位数填充缺失"
                else:
                    self.df[col] = self.df[col].fillna("未知/未填写")
                    deal_method[col] = "分类文本列，使用「未知/未填写」填充"

        self.df = self.df.drop(columns=drop_cols)

        for col, method in deal_method.items():
            print(f"列 {col} 处理方式: {method}")

        return self.df

    def handle_outlier(self, mode="clip"):
        col_threshold = {}
        for col in self.df.columns:
            if not is_numeric_dtype(self.df[col]):
                continue
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - self.iqr_scale * IQR
            upper = Q3 + self.iqr_scale * IQR

            col_threshold[col] = {"lower": lower, "upper": upper}
            outlier_mask = (self.df[col] < lower) | (self.df[col] > upper)
            print(f"{col} | 下限:{lower:.2f} 上限:{upper:.2f} 异常数量:{outlier_mask.sum()}")

        if mode == "clip":
            for col, info in col_threshold.items():
                self.df[col] = self.df[col].clip(info["lower"], info["upper"])
        elif mode == "drop":
            total_mask = pd.Series(False, index=self.df.index)
            for col, info in col_threshold.items():
                mask = (self.df[col] < info["lower"]) | (self.df[col] > info["upper"])
                total_mask = total_mask | mask
            self.df = self.df[~total_mask]

        return self.df

    def run_full_clean(self, outlier_mode="clip") -> pd.DataFrame:
        print("======== 开始缺失值清洗 ========")
        self.handle_missing_value()
        print("\n======== 开始异常值IQR清洗 ========")
        self.handle_outlier(mode=outlier_mode)
        return self.df


if __name__ == "__main__":
    # 修改成你的csv路径
    raw_df = pd.read_csv(R"D:\wx26.7.14\auto_clean_project\raw_data\customer_chat_raw.csv", encoding="utf-8-sig")
    cleaner = AutoDataCleaner(raw_df, col_missing_drop_threshold=0.5, iqr_scale=1.5)
    clean_result = cleaner.run_full_clean(outlier_mode="clip")

    # 导出清洗后文件
    out_path = R"D:\wx26.7.14\auto_clean_project\clean_data\customer_clean.csv"
    clean_result.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("\n清洗完成，已输出 customer_clean.csv")
    print("清洗后行数：", len(clean_result))