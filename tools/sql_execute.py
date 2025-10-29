from collections.abc import Generator
from typing import Any
import re
import json
import pandas as pd
from io import BytesIO

from sqlalchemy import create_engine, text
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from tools.db_utils import fix_db_uri_encoding


class SQLExecuteTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        db_uri = tool_parameters.get("db_uri") or self.runtime.credentials.get("db_uri")
        if not db_uri:
            raise ValueError("Database URI is not provided.")
        
        db_uri = fix_db_uri_encoding(db_uri)
        query = tool_parameters.get("query").strip()
        format = tool_parameters.get("format", "json")
        config_options = tool_parameters.get("config_options") or '{"pool_size": 1, "max_overflow": 0, "pool_pre_ping": true, "pool_recycle": 3600}'
        
        try:
            config_options = json.loads(config_options)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format for Connect Config")
        
        # 创建引擎
        engine = create_engine(db_uri, **config_options)
        
        try:
            if re.match(r'^\s*(SELECT|WITH)\s+', query, re.IGNORECASE):
                # 使用 pandas 读取数据
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
                # 执行非查询语句
                with engine.begin() as conn:
                    result = conn.execute(text(query))
                    affected_rows = result.rowcount
                    yield self.create_text_message(
                        f"Query executed successfully. Affected rows: {affected_rows}"
                    )
                    
        except Exception as e:
            yield self.create_text_message(f"Error: {str(e)}")
            
        finally:
            # 确保连接池被完全释放
            engine.dispose()
