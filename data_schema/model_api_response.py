'''
Author: WLZ
Date: 2024-04-08 10:09:49
Description: 
'''
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, Any
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

T = TypeVar('T')

class ResponseModel(BaseModel, Generic[T]):
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="Success", description="消息说明")
    data: Optional[T] = Field(default=None, description="响应数据")

def response_model(data: Any = None, message: str = "Success", code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=code,
        content=jsonable_encoder(ResponseModel(code=code, message=message, data=data))
    )
