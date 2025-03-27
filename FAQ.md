# FAQ

## 1. 错误提示No module named 'MySQLdb'
你是应该是用`mysql+pymysql://`去连接，而不是`mysql://`

## 2. 密码中有 `@` 怎么办
`@` 是URL中的保留字符，需要使用 `%40` 代替，例如 `123%40456`

## 3. `text2sql`工具生成的sql语句无法运行
主要是模型的指令遵循能力不强，生成的sql格式不准确，建议换模型。或者针对它生成的sql语句，加一个代码节点进行修改，目前常见的模型生成sql语句错误有前面多了`sql`字符串，生成的sql都有`limit 5`，双引号格式问题等。

## 4. 安装本地插件或github版本报错 `PluginDaemonBadRequestError`
找环境变量设置 `FORCE_VERIFYING_SIGNATURE=false`

## 5. 如何安装离线版本
参考 https://github.com/junjiem/dify-plugin-repackaging

## 6. 数据库连接不上
一般是数据库地址不对，肯定不能填`localhost`，因为插件都是运行在容器内的，localhost也会指向容器内部，你要解决的是容器内如何连接你的宿主机或者你宿主机所在的局域网，询问大模型怎么解决这个问题

## 7. `sql_execute` 工具输出为json，但下个节点只能选择text和files
dify每个节点对接收的变量类型有限制，比如`直接回复`这个节点只能接收text和files类型的变量，可以在其前面加个`code`节点之类的转换一下

## 8. oracle连接问题
参考 https://docs.sqlalchemy.org/en/20/dialects/oracle.html#module-sqlalchemy.dialects.oracle.oracledb