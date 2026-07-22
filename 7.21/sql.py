import pymysql

class MysqlUtil:
  def __init__(self):
    db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '123456',
            'database': 'text',
            'charset': 'utf8mb4'
        }
    self.conn = pymysql.connect(**db_config)
    self.cursor =self.conn.cursor()

     # 查询方法：返回所有数据，修复拼写aegs→args
  def query(self, sql, args=None):
      self.cursor.execute(sql, args or [])
      return self.cursor.fetchall()  # 原来你只返回行数，拿不到数据

    # 增删改执行
  def execute(self, sql, args=None):
      self.cursor.execute(sql, args or [])
      self.conn.commit()
      return self.cursor.rowcount  # 返回影响行数

  def close(self):
      self.cursor.close()
      self.conn.close()

if __name__ == '__main__':
  mysql = MysqlUtil()
  sql = "select * from user"
  # query直接返回结果，不用再cursor.fetchall()
  res = mysql.query(sql)
  print(res)
  mysql.close()