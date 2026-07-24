### 7.24 Agent

#### 1.数据清洗：

##### 1.1  提取文件

    import pandas as pd
    
    # 读取csv文件
    df = pd.read_csv('job.csv', encoding='utf-8') #dataframe:pandas的DataFrame对象
    # df = pd.read_csv('job.csv', encoding='gbk')
    # print(df.head())
    # print(df.info())
    # print(df.describe())
    
    # 读取txt文件
    df_txt = pd.read_csv('data.txt', sep=',')
    # print(df_txt.head())
    # print(df_txt.info())
    # print(df_txt)
    
    # 读取excel文件 （需 pip install openpyxl）
    df_excel = pd.read_excel('job.xlsx')
    print(df_excel.head())
    print(df_excel.info())
    print(df_excel)

##### 1.2 数据的全局体验



##### 1.3课堂任务

### 任务要求：

1. 使用 `try-except` 处理不存在的文件读取。
2. 打印出每个文件的**缺失率最高的列**及其比例。
3. 统计每个文件中**“薪资” 为负数**的行有多少条。
   
   

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

### 3. 处理数据

##### 3.1 重复值和字符规范、

##### （1）重复值处理

- df.suplicated      
  
  * 作用：返回布尔 Series，**标记每一行是否为重复行**
  * 规则：重复行中，**第一次出现标记 False，后续重复的标记 True**

- df.drop_duplicates()
  删除全部重复行，**默认保留第一次出现的数据**
  常用参数：

- * `subset=["id","name"]`：只依据指定**若干列**判断是否重复
  
  * `keep="last"`：保留**最后一条**重复数据，删除前面重复记录
    
    # 按id、name两列去重，保留重复组最后一行
    
    df = df.drop_duplicates(subset=["id","name"], keep="last")
    
        subset=None：默认对比整行所有列；
        如果写 subset=["姓名","城市"]，就只拿这几列判断是否重复
        
        * `keep='first'`（默认）
          
          > 重复多条数据里：**第一条标记 False（不重复），后面重复的全部标记 True**
          
        * `keep='last'`
          
          > 重复多条数据里：**最后一条标记 False，前面重复行标记 True**

    `subset=None`：默认对比**整行所有列**；
    如果写 `subset=["姓名","城市"]`，就只拿这几列判断是否重复
    
        import pandas as pdimport numpy as npdf = pd.DataFrame(
        {
        "姓名": ["张三", "张三", "李四", "王五", "赵六",np.nan],
        "籍贯": ["北京", "北京", "上海", "京", "北京", "深圳"],
        "年龄": [25, 25, 150, -5, 28,25],
        "薪资": [8000, 8000, 12000, "10k", 15000,10000]
        })



##### （2）字符规范

- 方式 1：直接删除异常数据（样本少的时候使用）

    # 保留 0<年龄<120 的行
    df_clean = df[(df["年龄"] > 0) & (df["年龄"] < 120)]
    print("\n====删除年龄异常之后的数据====")
    print(df_clean)

- 方式 2：异常值修改为缺失值 NaN，后续统一填充

    # 将年龄异常的单元格设置为np.nan
    df.loc[(df["年龄"] <=0)|(df["年龄"]>=120), "年龄"] = np.nan
    print("\n====异常年龄改为空值====")
    print(df)
    
    # 使用该列均值填充缺失
    df["年龄"] = df["年龄"].fillna(df["年龄"].mean())
    print("\n====均值填充完成====")
    print(df)

- 方式 3：固定值替换异常

    df.loc[(df["年龄"] <=0)|(df["年龄"]>=120), "年龄"] = 30

- 方式4：新增一列标记异常（保留全部原始数据，只打标签）

    df["年龄是否异常"] = ((df["年龄"] <= 0) | (df["年龄"] >= 120))
    print("\n====新增异常标记列====")
    print(df)


