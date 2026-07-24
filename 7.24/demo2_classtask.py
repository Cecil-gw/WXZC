import pandas as pd

def analyze_file(file_path):
  try:
     df = pd.read_csv(file_path, encoding="utf-8")
     print(df.isnull())
     null_count=df.isnull().sum()
     print(null_count)

     totals_rows = len(df)
     print("缺失率:",null_count/totals_rows)

     max_col = (null_count/totals_rows).idxmax()
     print("缺失率最高的列:",max_col)
     print("缺失率最高的列缺失率:",null_count[max_col]/totals_rows)


  except FileNotFoundError:
    print("File not found.")


if __name__ == "__main__":
  file_path = "D:/wx26.7.14/data/data/job.csv"
  analyze_file(file_path)