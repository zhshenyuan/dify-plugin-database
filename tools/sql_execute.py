from collections.abc import Generator
from typing import Any, Dict
import re
import json
import pandas as pd
from io import BytesIO
from threading import Lock

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from tools.db_utils import fix_db_uri_encoding


class SQLExecuteTool(Tool):
    # 类级别的引擎缓存
    _engines: Dict[str, Engine] = {}
    _lock = Lock()
    
    @classmethod
    def get_engine(cls, db_uri: str, config_options: dict) -> Engine:
        """获取或创建数据库引擎（线程安全）"""
        # 使用 db_uri 作为缓存键
        cache_key = db_uri
        
        with cls._lock:
            if cache_key not in cls._engines:
                cls._engines[cache_key] = create_engine(db_uri, **config_options)
            return cls._engines[cache_key]
    
    @classmethod
    def dispose_engine(cls, db_uri: str):
        """释放特定的数据库引擎"""
        with cls._lock:
            if db_uri in cls._engines:
                cls._engines[db_uri].dispose()
                del cls._engines[db_uri]
    
    @classmethod
    def dispose_all_engines(cls):
        """释放所有缓存的引擎"""
        with cls._lock:
            for engine in cls._engines.values():
                engine.dispose()
            cls._engines.clear()
    
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        db_uri = tool_parameters.get("db_uri") or self.runtime.credentials.get("db_uri")
        if not db_uri:
            raise ValueError("Database URI is not provided.")
        
        db_uri = fix_db_uri_encoding(db_uri)
        query = tool_parameters.get("query").strip()
        format = tool_parameters.get("format", "json")
        config_options = tool_parameters.get("config_options") or '{"pool_size": 5, "max_overflow": 10, "pool_pre_ping": true, "pool_recycle": 3600}'
        
        try:
            config_options = json.loads(config_options)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format for Connect Config")
        
        # 获取复用的引擎
        engine = self.get_engine(db_uri, config_options)
        
        try:
            if re.match(r'^\s*(SELECT|WITH)\s+', query, re.IGNORECASE):
                with engine.connect() as conn:
                    df = pd.read_sql(text(query), conn)
                
                if format == "json":
                    result = df.to_dict(orient='records')
                    yield self.create_json_message({"result": result})
                    
                elif format == "md":
                    result = df.to_markdown(index=False)
                    yield self.create_text_message(result)
                    
                elif format == "csv":
                    result = df.to_csv(index=False).encode()
                    yield self.create_blob_message(
                        result, meta={"mime_type": "text/csv", "filename": "result.csv"}
                    )
                    
                elif format == "yaml":
                    import yaml
                    result = yaml.dump(df.to_dict(orient='records')).encode()
                    yield self.create_blob_message(
                        result, meta={"mime_type": "text/yaml", "filename": "result.yaml"}
                    )
                    
                elif format == "xlsx":
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    result = output.getvalue()
                    yield self.create_blob_message(
                        result,
                        meta={
                            "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            "filename": "result.xlsx",
                        },
                    )
                    
                elif format == "html":
                    result = df.to_html(index=False).encode()
                    yield self.create_blob_message(
                        result, meta={"mime_type": "text/html", "filename": "result.html"}
                    )
                else:
                    raise ValueError(f"Unsupported format: {format}")
            else:
                with engine.begin() as conn:
                    result = conn.execute(text(query))
                    affected_rows = result.rowcount
                    yield self.create_text_message(
                        f"Query executed successfully. Affected rows: {affected_rows}"
                    )
                    
        except Exception as e:
            yield self.create_text_message(f"Error: {str(e)}")
