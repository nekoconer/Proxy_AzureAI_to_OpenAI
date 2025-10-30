import psycopg2
from datetime import datetime

class PostgresCRUD:
    def __init__(self):
        self.conn=None
        self.db_config = {
        "host": "127.0.0.1",
        "port": "5432",
        "database": "apiusage",
        "user": "presoft",
        "password": "dev001"
        }
        self._create_connect()
                   
    def _create_connect(self):
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.autocommit = False  # 手动提交
        except psycopg2.OperationalError:
            conn = psycopg2.connect(database="postgres", user="presoft", password="dev001")
            cur = conn.cursor()
            try:
                cur.execute("CREATE DATABASE apiusage;")
            except psycopg2.errors.DuplicateDatabase:
                pass  # 数据库已存在
            conn.commit()
            conn.close()
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.autocommit = False  # 手动提交
            self.create_table()
        
        
    def execute(self, sql, params=None, fetch=False):
        """
        通用执行函数
        :param sql: SQL语句
        :param params: 参数元组或列表
        :param fetch: 是否查询返回结果
        :return: 如果 fetch=True 返回查询结果，否则返回影响行数
        """
        with self.conn.cursor() as cur:
            try:
                cur.execute(sql, params)
                if fetch:
                    result = cur.fetchall()
                    self.conn.commit()
                    return result
                else:
                    affected = cur.rowcount
                    self.conn.commit()
                    return affected
            except Exception as e:
                self.conn.rollback()
                #print("执行失败:", e)
                raise
    def create_table(self):
        with self.conn.cursor() as cur:
            create_company_key = """
            CREATE TABLE IF NOT EXISTS company_key (
                company varchar(255),
                "key" varchar(255) NOT NULL,
                prompt_usage integer,
                output_usage integer,
                total_usage integer,
                remain_usage integer,
                datatime timestamp without time zone,
                chat_used integer,
                chat_remain integer,
                PRIMARY KEY("key")
            );
            """
            create_use_kind = """
            CREATE TABLE IF NOT EXISTS use_kind (
                "key" varchar(255),
                prompt_usage integer,
                output_usage integer,
                total_usage integer,
                model_kind varchar(32),
                use_kind varchar(32),
                mission_name varchar(32),
                datatime timestamp without time zone
            );
            """
            cur.execute(create_company_key)
            cur.execute(create_use_kind)
            self.conn.commit()

    def close(self):
        self.conn.close()
       
def excute_sql(sql,params,fetch=True):
    try:
        db = PostgresCRUD()
        rows = db.execute(sql,params,fetch)
        return rows
    except Exception as e:
        print(f"数据库执行时出错:{str(e)}")
        raise
    finally:
        if db:
            db.close()
    
        
if __name__ =="__main__":
    db = PostgresCRUD()
    #insert_sql = "INSERT INTO company_key (company, key,prompt_usage,output_usage,total_usage,data_time) VALUES (%s, %s, %s, %s, %s, %s)"
    #db.execute(insert_sql, ("PAI", "PAI-test1232312lrh1lk41",11,12,23,datetime.now()))

    #insert_sql = "INSERT INTO company_key (company, key) VALUES (%s, %s)"
    #select_sql_a = "SELECT key FROM company_key"
    #select_sql_b = "SELECT key_a FROM key_usage"
    #params=("PAI_test_11","PAI-dkasjfioahflaksdlkahwdialdan")
    now = datetime.now()
    prompt_usage=10
    output_usage=10
    total_usage =2000000
    key="PAI-0936b722cd324d21a32d4391e350cf38"
    update_sql = "UPDATE company_key SET prompt_usage = prompt_usage +%s,output_usage = output_usage +%s,total_usage=total_usage+%s,remain_usage=remain_usage-%s,datatime=%s WHERE key=%s;"
    data_time =datetime.now()
    params=(prompt_usage,output_usage,total_usage,total_usage,data_time,key)
    #result = excute_sql(select_sql_b,params)
    #print(f"xxx:{result}")
    result = excute_sql(update_sql,params,False)
    print(f"xxx:{result}")