import pymysql

conn = pymysql.connect(
    host="192.168.0.45",
    port=3306,
    user="root",
    password="123456",
    database="student_db",
    charset="utf8mb4"
)

cursor = conn.cursor()

# 1. 新建教师表 teacher
create_teacher_sql = """
CREATE TABLE IF NOT EXISTS teacher (
    tid INT PRIMARY KEY AUTO_INCREMENT COMMENT '教师编号',
    tname VARCHAR(20) NOT NULL COMMENT '教师姓名',
    subject VARCHAR(20) COMMENT '授课科目',
    salary INT COMMENT '薪资',
    entry_time DATETIME DEFAULT NOW() COMMENT '入职时间'
) COMMENT '教师信息表';
"""
cursor.execute(create_teacher_sql)
print("teacher表创建完成")

# 2. 查看库中全部表（会同时显示student、teacher）
cursor.execute("SHOW TABLES;")
all_tables = cursor.fetchall()
print("当前库所有表：", all_tables)

# 3. 查看teacher表结构
cursor.execute("DESC teacher;")
table_struct = cursor.fetchall()
print("teacher表结构：", table_struct)

# 4. 查询teacher表数据（刚建完是空的）
cursor.execute("SELECT * FROM teacher;")
data = cursor.fetchall()
print("teacher表内数据：", data)

# 释放资源
cursor.close()
conn.close()