from datetime import datetime
import os,sys
import json
import uuid
from fastapi.responses import JSONResponse

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from database.db import excute_sql

ROOT_DIR_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.join(ROOT_DIR_PATH,"use_cache")


def output_token(usage_data, model_kind, api_key, use_kind, mission):
    if hasattr(usage_data, "to_dict"):
        usage_data = usage_data.to_dict()
    elif not isinstance(usage_data, dict):
        usage_data = usage_data.__dict__
    chat_prompt_tokens = usage_data.get("prompt_tokens")
    chat_total_tokens = usage_data.get("total_tokens")
    chat_output_tokens = chat_total_tokens-chat_prompt_tokens
    data_time = datetime.now()
    #timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # new_entry = {
    #     "prompt": chat_prompt_tokens,
    #     "output": chat_output_tokens,
    #     "total": chat_total_tokens,
    #     "data": timestamp
    # }
    # output_path = f"{api_key}.json"
    # WORKING_DIR = os.path.join(ROOT_DIR, output_path)
    # if not os.path.exists(ROOT_DIR):
    #     os.makedirs(ROOT_DIR, exist_ok=True)
    # try:
    #     with open(WORKING_DIR, "r", encoding="utf-8") as f:
    #         data = json.load(f)  # 读取已有 dict
    # except FileNotFoundError:
    #     data = {}
    # data.setdefault(use_mode, []).append(new_entry)
    # with open(WORKING_DIR, "w", encoding="utf-8") as f:
    #     json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"{model_kind}_token_usage is prompt:{chat_prompt_tokens},output:{chat_output_tokens},total:{chat_total_tokens}")
    update_token_key(api_key,chat_prompt_tokens,chat_output_tokens,chat_total_tokens,data_time)
    insert_usekind_token(api_key,chat_prompt_tokens,chat_output_tokens,chat_total_tokens,model_kind,use_kind,mission,data_time)
    
def check_pai_key(key):
    if key.startswith("PAI-"):
        res = search_key(key)
        if len(res):
            #05：remain token 08：remain chat
            return res[0][8]
        else:
            return False
    else:
        return False

def check_remain(res):
        if res <=0:
           return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "message": "API token is out of charge!",
                    "type": "insufficient_quota",
                    "param": None,
                    "code": "insufficient_quota"
                }
            }
        )
        else:
            return True 

def final_check(res,x_custom_header):
    if res is False:
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "message": "API key is wrong!",
                    "type": "insufficient_quota",
                    "param": None,
                    "code": "insufficient_quota"
                }
            }
        )
    else:
        if x_custom_header == "chat":
            res2 = check_remain(res)
            if res2 is True:
                return True
            else:
                return res2
        elif x_custom_header == "RAG":
            return True
        else:
            print("Header is not provided")
            return True
            # return JSONResponse(
            # status_code=429,
            # content={
            #     "error": {
            #         "message": "Error Header",
            #         "type": "insufficient_quota",
            #         "param": None,
            #         "code": "insufficient_quota"
            #             }
            #         }
            #     )
def insert_usekind_token(api_key,chat_prompt_tokens,chat_output_tokens,chat_total_tokens,model_kind,use_kind,mission,data_time):
    insert_sql = "INSERT INTO use_kind (key,prompt_usage,output_usage,total_usage,model_kind,use_kind,mission_name,datatime) VALUES (%s, %s,%s,%s,%s,%s,%s,%s)" 

    params=(api_key,chat_prompt_tokens,chat_output_tokens,chat_total_tokens,model_kind,use_kind,mission,data_time)
    excute_sql(insert_sql,params,False)


def create_company_key(company_name,num=1000000,chat_num=200):
    insert_sql = "INSERT INTO company_key (company, key,prompt_usage,output_usage,total_usage,remain_usage,datatime,chat_used,chat_remain) VALUES (%s, %s,%s,%s,%s,%s,%s,%s,%s)" 
    uuid4 = uuid.uuid4()
    u_no_dash = str(uuid4).replace('-', '')
    key = f"PAI-{u_no_dash}"
    data_time = datetime.now()
    params=(company_name,key,0,0,0,num,data_time,0,chat_num)
    params=(company_name,key,0,0,0,num,data_time,0,chat_num)
    excute_sql(insert_sql,params,False)
    return key

def delete_company_key(company_name,key):
    delete_sql = "DELETE FROM company_key WHERE company = %s AND key=%s" 
    params=(company_name,key)
    excute_sql(delete_sql,params,False)

def add_remain_key(company_name,key,add_num):
    add_remain_sql = "UPDATE company_key SET remain_usage = remain_usage + %s,datatime=%s WHERE company = %s AND key=%s" 
    data_time = datetime.now()
    params=(add_num,data_time,company_name,key)
    excute_sql(add_remain_sql,params,False)
    
def add_remain_chat(company_name,key,add_num=200):
    add_remain_sql = "UPDATE company_key SET chat_remain = chat_remain + %s,datatime=%s WHERE company = %s AND key=%s" 
    data_time = datetime.now()
    params=(add_num,data_time,company_name,key)
    excute_sql(add_remain_sql,params,False)
    
def add_remain_chat(company_name,key,add_num=200):
    add_remain_sql = "UPDATE company_key SET chat_remain = chat_remain + %s,datatime=%s WHERE company = %s AND key=%s" 
    data_time = datetime.now()
    params=(add_num,data_time,company_name,key)
    excute_sql(add_remain_sql,params,False)

def update_token_key(key,prompt_usage,output_usage,total_usage,data_time):
    update_sql = "UPDATE company_key SET prompt_usage = prompt_usage +%s,output_usage = output_usage +%s,total_usage=total_usage+%s,remain_usage=remain_usage-%s,datatime=%s WHERE key=%s;"
    params=(prompt_usage,output_usage,total_usage,total_usage,data_time,key)
    excute_sql(update_sql,params,False)

def update_chat_key(key):
    data_time = datetime.now()
    update_sql = "UPDATE company_key SET chat_used = chat_used + 1,chat_remain = chat_remain - 1,datatime=%s WHERE key=%s;"
    params=(data_time,key)
    excute_sql(update_sql,params,False)

def search_key(key):
    select_sql="SELECT * FROM company_key WHERE key = %s"
    params=(key,)
    res = excute_sql(select_sql,params)
    #print(res)
    return res

def show_all_keys(company=None):
    if company is None:
        select_sql ="SELECT * FROM company_key"
        res = excute_sql(select_sql,None)
        return res
    else:
        select_sql = "SELECT * FROM company_key WHERE company = %s"
        params=(company,)
        res = excute_sql(select_sql,params)
        return res

if __name__=="__main__":
    print(show_all_keys("PAI"))
