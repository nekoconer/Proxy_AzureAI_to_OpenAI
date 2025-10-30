from fastapi import FastAPI, Request,Body
import httpx
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from openai import AzureOpenAI,AsyncAzureOpenAI
import json
import logging
import time
from dotenv import load_dotenv
load_dotenv()
from utils.utils import output_token,create_company_key,delete_company_key,add_remain_key,check_pai_key,final_check,show_all_keys,update_chat_key,add_remain_chat
from pydantic import BaseModel, ConfigDict
from typing import Any

from utils.model import CreateKeyRequest,DeleteKeyRequest,AddKeyRequest,KeyStatusRequest

class ResponseEntity(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    status_code: int
    message: Any

# 确保 logs 文件夹存在（可选）
home_dir = os.path.expanduser("~")
path = os.path.join(home_dir, "logs")
os.makedirs(path, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(path,"UsageMonitoring.log"),  # 你可以根据需要修改路径
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"  # ✅ 关键设置
)

app = FastAPI()
AZURE_DEPLOYMENT_CHAT_MODEL = os.getenv("AZURE_DEPLOYMENT_CHAT_MODEL")
AZURE_DEPLOYMENT_EMBEDDING_MODEL = os.getenv("AZURE_DEPLOYMENT_EMBEDDING_MODEL")
AZURE_BASE = os.getenv("AZURE_BASE")
AZURE_KEY = os.getenv("AZURE_KEY")
# AZURE_DEPLOYMENT_URL=f"/openai/deployments/{AZURE_DEPLOYMENT_CHAT_MODEL}/chat/completions"
# AZURE_EMBEDDING_URL=f"/openai/deployments/{AZURE_DEPLOYMENT_EMBEDDING_MODEL}/embeddings"
AZURE_API_VERSION  =os.getenv("AZURE_API_VERSION")

AZURE_DEPLOYMENT_CHAT_ANSWER_MODEL = os.getenv("AZURE_DEPLOYMENT_CHAT_ANSWER_MODEL")
AZURE_ANSWER_BASE = os.getenv("AZURE_ANSWER_BASE")
AZURE_KEY_ANSWER = os.getenv("AZURE_KEY_ANSWER")

azure_client = AsyncAzureOpenAI(
    api_key=AZURE_KEY,
    api_version=AZURE_API_VERSION,  # e.g. "2025-04-01-preview"
    azure_endpoint=AZURE_BASE  # e.g. "https://xxx-eastus2.cognitiveservices.azure.com/"
)

azure_client_answer = AsyncAzureOpenAI(
    api_key=AZURE_KEY_ANSWER,
    api_version=AZURE_API_VERSION,  # e.g. "2025-04-01-preview"
    azure_endpoint=AZURE_ANSWER_BASE  # e.g. "https://xxx-eastus2.cognitiveservices.azure.com/"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，生产环境中应该设置具体的源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

@app.get("/api/v1/models")
async def get_models():
    current_timestamp = int(time.time())
    return JSONResponse(content={
        "object": "list",
        "data": [
            {
            "id": "text-embedding-3-large",
            "object": "model",
            "created": current_timestamp,
            "owned_by": "openai"
            },
            {
            "id": "gpt-4.1-mini",
            "object": "model",
            "created": current_timestamp,
            "owned_by": "openai"
            }
        ]
    })
# ---------------- Chat Completions ----------------
@app.post("/api/v1/chat/completions")
async def chat_completions(request: Request):
    data = await request.json()
    headers = request.headers
    api_key = headers.get("Authorization", "").replace("Bearer ", "")
    x_custom_header = headers.get("X-Custom-Header")
    x_mission_header = headers.get("X-Mission-Header")
    print(f"apikey:{api_key},custom_header:{x_custom_header},mission_header:{x_mission_header}")

    # 校验逻辑
    try:
        res = check_pai_key(api_key)
        flag = final_check(res, x_custom_header)
    except Exception:
        return JSONResponse(
            status_code=429,
            content={
                "error": {"message": "proxy DB is not connected!", "type": "insufficient_quota",
                          "param": None, "code": "insufficient_quota"}
            }
        )

    if flag is not True:
        return flag
    azure_client_tmp = azure_client
    model_tmp = AZURE_DEPLOYMENT_CHAT_MODEL
    # Comment out the following four lines if you don't need to switch the answer model.
    if x_mission_header == "AI_chat_answer":
        update_chat_key(api_key)
        azure_client_tmp = azure_client_answer
        model_tmp = AZURE_DEPLOYMENT_CHAT_ANSWER_MODEL
    
    data.pop("model", None)
    # -------- 流式响应 --------
    if data.get("stream") is True:
        try:
            async def event_generator():
                async with azure_client_tmp.chat.completions.with_streaming_response.create(
                    **data,
                    model=model_tmp,
                    stream_options={"include_usage": True}
                ) as response:
                    async for chunk in response.iter_bytes():
                        chunk_text = chunk.decode('utf-8')
                        #print(f"chunktext:{chunk_text}")
                        # 可选：日志记录
                        if chunk_text.startswith("data:"):
                            line = chunk_text[len('data:'):].strip()
                            if line == "[DONE]":
                                yield "data: [DONE]\n\n"
                                break
                            parsed_data = json.loads(line)
                            usage_data = parsed_data.get("usage")
                            if usage_data:
                                output_token(usage_data,"chat",api_key,x_custom_header,x_mission_header)
                                continue
                            choices = parsed_data.get("choices", [])
                            if choices and isinstance(choices, list):
                                delta = choices[0].get("delta", {})
                                content = delta.get("content")
                                if content:
                                    yield f"data: {line}\n\n"
        except json.JSONDecodeError:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "message": "Json format is error!",
                        "type": "insufficient_quota",
                        "param": None,
                        "code": "insufficient_quota"
                    }
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "message": str(e),
                        "type": "insufficient_quota",
                        "param": None,
                        "code": "insufficient_quota"
                    }
                }
            )
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )

    # -------- 非流式响应 --------
    else:
        resp = await azure_client_tmp.chat.completions.create(
            **data,
            model=model_tmp
        )
        usage = resp.usage
        if usage:
            output_token(usage, "chat", api_key, x_custom_header, x_mission_header)
        return resp.model_dump()


# ---------------- Embeddings ----------------
@app.post("/api/v1/embeddings")
async def embedding_completions(request: Request):
    data = await request.json()
    data.pop("model", None)
    headers = request.headers
    api_key = headers.get("Authorization", "").replace("Bearer ", "")
    x_custom_header = headers.get("X-Custom-Header")
    x_mission_header = headers.get("X-Mission-Header")
    print(f"apikey:{api_key}")
    print(f"custom_header:{x_custom_header}")
    print(f"mission_header:{x_mission_header}")

    # 校验逻辑
    try:
        res = check_pai_key(api_key)
        flag = final_check(res, x_custom_header)
    except Exception:
        return JSONResponse(
            status_code=429,
            content={
                "error": {"message": "proxy DB is not connected!", "type": "insufficient_quota",
                          "param": None, "code": "insufficient_quota"}
            }
        )

    if flag is not True:
        return flag

    try:
        resp = await azure_client.embeddings.create(
            **data,
            model=AZURE_DEPLOYMENT_EMBEDDING_MODEL  # ⚠️ Azure 部署名
        )
        usage = resp.usage
        if usage:
            output_token(usage, "embedding", api_key, x_custom_header, x_mission_header)
        return resp.model_dump()
    except Exception as e:
        return JSONResponse(
            status_code=429,
            content={
                "error": {"message": str(e), "type": "insufficient_quota",
                          "param": None, "code": "insufficient_quota"}
            }
        )

@app.post("/api/compact/create_key")
def create_key(data: CreateKeyRequest):
    try:
        key = create_company_key(data.company,data.num)
        return ResponseEntity(
            message=f"{key}",
            status_code=200
        ) 
    except Exception as e:
        logging.info(f"创建key时出错:{str(e)}")
        return ResponseEntity(
            message=str(e),
            status_code=500
        )

@app.delete("/api/compact/delete_key")
def delete_key(data: DeleteKeyRequest):
    try:
        key = delete_company_key(data.company,data.key)
        return ResponseEntity(
            message=f"Delete Successfully",
            status_code=200
        ) 
    except Exception as e:
        logging.info(f"创建key时出错:{str(e)}")
        return ResponseEntity(
            message=str(e),
            status_code=500
        )

@app.post("/api/compact/add_remain")
def add_remain(data:AddKeyRequest):
    try:
        key = add_remain_key(data.company,data.key,data.add_num)
        return ResponseEntity(
            message=f"Add Remain Successfully",
            status_code=200
        ) 
    except Exception as e:
        logging.info(f"增加keytoken时出错:{str(e)}")
        return ResponseEntity(
            message=str(e),
            status_code=500
        )
        
@app.post("/api/compact/add_chat_remain")
def add_remain(data:AddKeyRequest):
    try:
        key = add_remain_chat(data.company,data.key,data.add_num)
        return ResponseEntity(
            message=f"Add Remain Successfully",
            status_code=200
        ) 
    except Exception as e:
        logging.info(f"增加key_chat时出错:{str(e)}")
        return ResponseEntity(
            message=str(e),
            status_code=500
        )
        
@app.post("/api/compact/keylists")
def return_keys_status(data:KeyStatusRequest):
    try:
        company_name = data.company
        if company_name=="ALL":
            result = show_all_keys()
        else:
            result = show_all_keys(data.company)
        return ResponseEntity(
                message=result,
                status_code=200
            )
    except Exception as e:
        logging.info(f"查询keylists出错:{str(e)}")
        return ResponseEntity(
            message=str(e),
            status_code=500
        )
    
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=7788)