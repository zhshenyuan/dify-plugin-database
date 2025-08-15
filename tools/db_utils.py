"""
数据库工具函数
"""
import re
from urllib.parse import quote_plus


def fix_db_uri_encoding(db_uri: str) -> str:
    """
    修复数据库 URI 中的特殊字符编码问题
    特别是处理密码中包含 @ 符号的情况
    
    Args:
        db_uri: 原始数据库 URI
        
    Returns:
        修复后的数据库 URI
        
    Examples:
        >>> fix_db_uri_encoding("postgresql://user:pass@word@localhost:5432/db")
        'postgresql://user:pass%40word@localhost:5432/db'
        
        >>> fix_db_uri_encoding("mysql://user:pass+word@localhost:3306/db")
        'mysql://user:pass%2Bword@localhost:3306/db'
    """
    try:
        # 使用更精确的正则表达式来解析数据库 URI
        # 格式: scheme://username:password@host:port/database
        import re
        
        # 匹配数据库 URI 的正则表达式
        # 使用非贪婪匹配来正确处理密码中的 @ 符号
        pattern = r'^([^:]+)://([^:]+):(.+)@([^:]+):(\d+)/(.+)$'
        match = re.match(pattern, db_uri)
        
        if match:
            scheme, username, password, host, port, database = match.groups()
            
            # 对用户名和密码进行 URL 编码
            encoded_username = quote_plus(username)
            encoded_password = quote_plus(password)
            
            # 重建 URI
            fixed_uri = f"{scheme}://{encoded_username}:{encoded_password}@{host}:{port}/{database}"
            return fixed_uri
        else:
            # 如果没有匹配到标准格式，尝试其他格式
            # 处理没有端口号的情况
            pattern_no_port = r'^([^:]+)://([^:]+):(.+)@([^/]+)/(.+)$'
            match = re.match(pattern_no_port, db_uri)
            
            if match:
                scheme, username, password, host, database = match.groups()
                
                # 对用户名和密码进行 URL 编码
                encoded_username = quote_plus(username)
                encoded_password = quote_plus(password)
                
                # 重建 URI
                fixed_uri = f"{scheme}://{encoded_username}:{encoded_password}@{host}/{database}"
                return fixed_uri
            else:
                # 如果都不匹配，返回原始 URI
                return db_uri
                
    except Exception:
        # 如果解析失败，返回原始 URI
        return db_uri 