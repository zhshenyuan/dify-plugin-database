from collections.abc import Generator
from typing import Any
import json

from sqlalchemy import create_engine, inspect
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage



class QueryTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        db_uri = tool_parameters.get("db_uri") or self.runtime.credentials.get("db_uri")
        engine = create_engine(db_uri)
        inspector = inspect(engine)

        tables = tool_parameters.get("tables")
        tables = tables.split(",") if tables else inspector.get_table_names()

        schema_info = {}
        with engine.connect() as _:

            for table_name in tables:
                try:
                    columns = inspector.get_columns(table_name)
                    schema_info[table_name] = [
                        {
                            "name": col["name"],
                            "type": str(col["type"]),
                            "nullable": col.get("nullable", True),
                            "default": col.get("default"),
                            "primary_key": col.get("primary_key", False),
                        }
                        for col in columns
                    ]
                except Exception as e:
                    schema_info[table_name] = f"Error getting schema: {str(e)}"
        yield self.create_text_message(json.dumps(schema_info, ensure_ascii=False))
