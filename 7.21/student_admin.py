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

  # 建库（原样不动，通用模板）
  def create_databases(self,sql,db_name):
    try:
      self.cursor.execute(sql)
      self.conn.commit()
      print(f"创建数据库{db_name}成功")
    except MySQLError as e:
      print(f"创建数据库{db_name}失败：{e}")

  def drop_databases(self,db_name):
    try:
      sql = f"DROP DATABASE IF EXISTS `{db_name}`;"
      self.cursor.execute(sql)
      self.conn.commit()
      print(f"删除数据库{db_name}成功")
    except MySQLError as e:
      print(f"删除数据库{db_name}失败：{e}")

  def use_databases(self,db_name):
    try:
      sql = f"use `{db_name}`;"
      self.cursor.execute(sql)
      self.conn.commit()
      print(f"使用数据库{db_name}成功")
    except MySQLError as e:
      print(f"使用数据库{db_name}失败：{e}")
    return self.cursor

  # 建表：原方法名、参数不变
  def create_tables(self,table_name,sql):
    try:
      self.cursor.execute(sql)
      self.conn.commit()
      print(f"创建表{table_name}成功")
    except MySQLError as e:
      print(f"创建表{table_name}失败：{e}")

  def update_tables(self,table_name, sql):
    try:
      self.cursor.execute(sql)
      self.conn.commit()
      print(f"更新表{table_name}成功")
    except MySQLError as e:
      print(f"更新表{table_name}失败：{e}")

  def drop_tables(self,table_name):
    try:
      sql = f"Drop table if exists `{table_name}`;"
      self.cursor.execute(sql)
      self.conn.commit()
      print(f"删除表{table_name}成功")
    except MySQLError as e:
      print(f"删除表{table_name}失败：{e}")

  # insert_data 参数顺序：table_name, sql, data
  def insert_data(self,table_name, sql, data):
    try:
      self.cursor.execute(sql, data)
      self.conn.commit()
      print(f"{table_name} 插入数据成功")
    except MySQLError as e:
      self.conn.rollback()
      print(f"{table_name} 插入数据失败：{e}")

  def select_data(self,table_name, sql, args=None):
    try:
      if args:
          self.cursor.execute(sql, args)
      else:
          self.cursor.execute(sql)
      result = self.cursor.fetchall()
      for row in result:
        print(row)
    except MySQLError as e:
      print(f"{table_name} 查询数据失败：{e}")
    return result

  def delete_data(self,table_name, sql, args=None):
    try:
      if args:
          self.cursor.execute(sql, args)
      else:
          self.cursor.execute(sql)
      self.conn.commit()
      print(f"{table_name} 删除数据成功")
    except MySQLError as e:
      self.conn.rollback()
      print(f"{table_name} 删除数据失败：{e}")

  def update_data(self,table_name, sql, data):
    try:
      self.cursor.execute(sql, data)
      self.conn.commit()
      print(f"{table_name} 更新数据成功")
    except MySQLError as e:
      self.conn.rollback()
      print(f"{table_name} 更新数据失败：{e}")

  def close(self):
    self.cursor.close()
    self.conn.close()


if __name__ == '__main__':
  student=Mysql()
  # 1、删除旧库，重建干净环境
  student.drop_databases("student")
  create_db_sql = "create database if not exists student default character set utf8mb4 collate utf8mb4_general_ci"
  student.create_databases(create_db_sql, "student")
  student.use_databases("student")

  # ====================== 需求1：创建两张数据表 班级表+学生表 ======================
  # 班级表 class_table
  create_class_sql = """
    CREATE TABLE IF NOT EXISTS `class_table` (
        id INT NOT NULL AUTO_INCREMENT COMMENT '主键自增',
        class_name VARCHAR(32) NOT NULL UNIQUE COMMENT '班级名 非空唯一',
        teacher VARCHAR(20) COMMENT '班主任',
        student_num INT DEFAULT 0 COMMENT '班级人数 默认0',
        PRIMARY KEY(id)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  """
  student.create_tables("class_table", create_class_sql)

  # 学生表 student_table
  create_student_sql ="""
  CREATE TABLE IF NOT EXISTS `student_table` (
        id INT NOT NULL AUTO_INCREMENT COMMENT '主键自增',
        name VARCHAR(32) NOT NULL UNIQUE COMMENT '姓名 非空唯一',
        age INT DEFAULT 0 COMMENT '年龄 默认0',
        class_id INT COMMENT '所属班级id',
        PRIMARY KEY(id)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  """
  student.create_tables("student_table", create_student_sql)
  print("===== 数据表创建完成 =====\n")

  # ====================== 需求2：批量新增测试数据 ======================
  # 先清空表防止唯一名称冲突
  student.cursor.execute("TRUNCATE TABLE class_table;")
  student.cursor.execute("TRUNCATE TABLE student_table;")
  student.conn.commit()

  # 批量插入3条班级
  insert_class_sql = "INSERT INTO `class_table` (class_name, teacher, student_num) VALUES(%s,%s,%s);"
  student.insert_data("class_table", insert_class_sql, ("Python一班", "周老师", 45))
  student.insert_data("class_table", insert_class_sql, ("Java二班", "张老师", 40))
  student.insert_data("class_table", insert_class_sql, ("Web三班", "李老师", 52))

  # 批量插入3条学生
  insert_stu_sql = "INSERT INTO `student_table` (name, age, class_id) VALUES(%s,%s,%s);"
  student.insert_data("student_table", insert_stu_sql, ("小明", 18, 1))
  student.insert_data("student_table", insert_stu_sql, ("小红", 19, 2))
  student.insert_data("student_table", insert_stu_sql, ("小刚", 18, 3))
  print("===== 批量测试数据插入完成 =====\n")

  # ====================== 需求3：条件查询、排序、分页 ======================
  # 3.1 条件查询：班级人数大于0
  print("===== 条件查询：人数大于0的班级 =====")
  student.select_data("class_table", "SELECT * FROM class_table WHERE student_num > 0;")

  # 3.2 按班级人数倒序排序
  print("\n===== 按人数倒序排序所有班级 =====")
  student.select_data("class_table", "SELECT * FROM class_table ORDER BY student_num DESC;")

  # 3.3 分页查询：第1页，每页1条
  print("\n===== 分页查询：第1页，每页1条 =====")
  student.select_data("class_table", "SELECT * FROM class_table LIMIT %s, %s;", (0, 1))

  # 3.4 模糊查询：班级名包含Python
  print("\n===== 模糊查询含Python班级 =====")
  student.select_data("class_table", "SELECT * FROM class_table WHERE class_name LIKE %s;", ("%Python%",))

  # ====================== 需求4：修改、删除数据 ======================
  # 4.1 修改Java二班班主任为【张老师】，人数改为35
  print("\n===== 修改Java二班信息 =====")
  update_sql = "UPDATE class_table SET teacher=%s, student_num=%s WHERE class_name=%s;"
  student.cursor.execute(update_sql, ("张老师", 35, "Java二班"))
  student.conn.commit()
  print("修改完成")

  # 4.2 删除任意一条学生数据（删除id=3的学生）
  print("\n===== 删除id=3学生 =====")
  del_sql = "DELETE FROM student_table WHERE id=%s;"
  student.cursor.execute(del_sql, (3,))
  student.conn.commit()
  print("删除完成")

  # ====================== 需求5：事务模拟：新增+修改，异常回滚 ======================
  print("\n===== 事务模拟（制造异常，自动回滚） =====")
  try:
      # 事务1：新增一个班级
      student.cursor.execute(insert_class_sql, ("C++四班", "赵老师", 38))
      # 事务2：修改Python一班人数为60
      student.cursor.execute("UPDATE class_table SET student_num=%s WHERE class_name=%s;", (60, "Python一班"))
      # 手动制造异常，触发回滚，两条操作全部失效
      1 / 0
      student.conn.commit()
      print("事务执行成功，数据已保存")
  except Exception as e:
      student.conn.rollback()
      print(f"事务异常 {e}，已执行回滚，所有操作未写入数据库")

  # ====================== 需求6：统计班级总数量、人数平均值 ======================
  print("\n===== 班级数据统计 =====")
  stat_sql = "SELECT COUNT(*) total_count, AVG(student_num) avg_num FROM class_table;"
  student.cursor.execute(stat_sql)
  total, avg = student.cursor.fetchone()
  print(f"班级总数量：{total}")
  print(f"班级平均人数：{round(avg, 2)}")

  student.close()