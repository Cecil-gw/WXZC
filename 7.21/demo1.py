import pymysql
from pymysql.err import MySQLError

# 连接数据库
class Mysql:
  def __init__(self):
    self.conn = pymysql.connect(
      host='localhost',
      user='root',
      password='123456',
      port=3306,
      database='student',
      charset="utf8mb4"
    )
    self.cursor = self.conn.cursor()

  def create_databases(self,sql,db_name):
    try:
      #if not exit
      self.cursor.execute(sql)
      self.conn.commit()
      print(f"创建数据库{db_name}成功")
    except MySQLError as e:
      print(f"创建数据库{db_name}失败")

  def drop_databases(self,db_name):
    try:
      sql = f"Drop database if exists `{db_name}`;"
      self.cursor.execute(sql)
      self.conn.commit()
      print(f"删除数据库{db_name}成功")
    except MySQLError as e:
      print(f"删除数据库{db_name}失败")

  def use_databases(self,db_name):
    try:
      sql = f"use `{db_name}`;"
      self.cursor.execute(sql)
      self.conn.commit()
      print(f"使用数据库{db_name}成功")
    except MySQLError as e:
      print(f"使用数据库{db_name}失败")
    return self.cursor

  def create_tables(self,table_name):
    try:
      sql = f"Create table if not exists `{table_name}`(id int(11) not null auto_increment, name varchar(255) not null, age int(11) not null, primary key(id));"
      self.cursor.execute(sql)
      self.conn.commit()
      print(f"创建表{table_name}成功")
    except MySQLError as e:
      print(f"创建表{table_name}失败")

  def update_tables(self,table_name):
    try:
      sql = f"Alter table `{table_name}` add column gender varchar(255) not null;"
      self.cursor.execute(sql)
      self.conn.commit()
      print(f"更新表{table_name}成功")
    except MySQLError as e:
      print(f"更新表{table_name}失败")

  def drop_tables(self,table_name):
    try:
      sql = f"Drop table if exists `{table_name}`;"
      self.cursor.execute(sql)
      self.conn.commit()
      print(f"删除表{table_name}成功")
    except MySQLError as e:
      print(f"删除表{table_name}失败")

  def insert_data(self,table_name,data):
    try:
      sql = f"Insert into `{table_name}`(name,age) values(%s,%s);"
      self.cursor.execute(sql,data)
      self.conn.commit()
      print(f"插入数据成功")
    except MySQLError as e:
      print(f"插入数据失败")

  def select_data(self,table_name):
    try:
      sql = f"Select * from `{table_name}`;"
      self.cursor.execute(sql)
      result = self.cursor.fetchall()
      for row in result:
        print(row)
    except MySQLError as e:
      print(f"查询数据失败")
    return result
  def delete_data(self,table_name):
    try:
      sql = f"Delete from `{table_name}`;"
      self.cursor.execute(sql)
      self.conn.commit()
      print(f"删除数据成功")
    except MySQLError as e:
      print(f"删除数据失败")

  def update_data(self,table_name,data):
    try:
      sql = f"Update `{table_name}` set name=%s,age=%s where id=%s;"
      self.cursor.execute(sql,data)
      self.conn.commit()
      print(f"更新数据成功")
    except MySQLError as e:
      print(f"更新数据失败")

    

  def close(self):
    self.cursor.close()
    self.conn.close()

if __name__ == "__main__":
  db = Mysql()
    # 1. 拼接建student库SQL，调用你自带的create_databases方法
    # create_db_sql = "CREATE DATABASE IF NOT EXISTS `student` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
    # db.create_databases(create_db_sql, "student")

    # # 2. 切换到student数据库
    # db.use_databases("student")

    # # 3. 创建班级表 class_table
    # create_class_sql = """
    # CREATE TABLE IF NOT EXISTS `class_table` (
    #     id INT NOT NULL AUTO_INCREMENT,
    #     class_name VARCHAR(32) NOT NULL UNIQUE,
    #     teacher VARCHAR(20),
    #     student_num INT DEFAULT 0,
    #     PRIMARY KEY(id)
    # ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    # """
    # try:
    #     db.cursor.execute(create_class_sql)
    #     db.conn.commit()
    #     print("班级表 class_table 创建成功")
    # except MySQLError as e:
    #     print(f"创建班级表失败：{e}")

    # # TRUNCATE 清空表并重置自增id，下次插入id从1开始
    # db.cursor.execute("TRUNCATE TABLE class_table;")
    # db.conn.commit()

    # # 4.插入2条班级数据
    # insert_sql = "INSERT INTO `class_table` (class_name, teacher, student_num) VALUES (%s, %s, %s);"
    # db.cursor.execute(insert_sql, ("高一1班", "王老师", 45))
    # db.cursor.execute(insert_sql, ("高二3班", "李老师", 52))
    # db.conn.commit()
    # print("成功插入2条班级数据\n")

    # # ② 查询1：所有班级
    # print("===== 查询全部班级 =====")
    # db.cursor.execute("SELECT * FROM class_table")
    # all_class = db.cursor.fetchall()
    # # 遍历打印班级名称、班主任
    # for row in all_class:
    #     print(f"班级：{row[1]}，班主任：{row[2]}")

    # # ③ 查询2：主键id=1的班级（现在能查到了）
    # print("\n===== 查询id=1的班级 =====")
    # db.cursor.execute("SELECT * FROM class_table WHERE id=%s", (1,))
    # one_class = db.cursor.fetchone()
    # if one_class:
    #     print(f"班级：{one_class[1]}，班主任：{one_class[2]}")
    # else:
    #     print("未查询到id=1的班级")

    # # ④ 查询3：人数大于0的班级
    # print("\n===== 查询人数大于0的班级 =====")
    # db.cursor.execute("SELECT * FROM class_table WHERE student_num > 0")
    # num_class = db.cursor.fetchall()
    # for row in num_class:
    #     print(f"班级：{row[1]}，班主任：{row[2]}，人数：{row[3]}")
  Insert_sql = "insert into class_table(class_name,teacher,student_num) values(%s,%s,%s);"

  db.conn.commit()


  sql="Select * from class_table order by student_num desc;"
  db.cursor.execute(sql)
  result = db.cursor.fetchall()
  for row in result:
    print(row)
  print("\n===== 2、分页查询 第1页，每页1条 =====")
  page = 1
  page_size = 1
  offset = (page - 1) * page_size
  sql_page = "SELECT * FROM class_table LIMIT %s, %s;"
  db.cursor.execute(sql_page, (offset, page_size))
  res_page = db.cursor.fetchall()
  for row in res_page:
      print(f"班级：{row[1]}，班主任：{row[2]}，人数：{row[3]}")

  # ===================== 3. 模糊查询含Python的班级 =====================
  print("\n===== 3、模糊查询班级名包含Python =====")
  sql_like = "SELECT * FROM class_table WHERE class_name LIKE %s;"
  db.cursor.execute(sql_like, ("%Python%",))
  res_like = db.cursor.fetchall()
  if res_like:
      for row in res_like:
          print(f"班级：{row[1]}，班主任：{row[2]}，人数：{row[3]}")
  else:
      print("无匹配班级")

  # ===================== 4. 统计总数量、平均人数 =====================
  print("\n===== 4、统计班级总数、平均人数 =====")
  sql_stat = "SELECT COUNT(*) total_count, AVG(student_num) avg_num FROM class_table;"
  db.cursor.execute(sql_stat)
  total, avg = db.cursor.fetchone()
  print(f"班级总数量：{total}")
  print(f"班级平均人数：{round(avg, 2)}")


  db.close()