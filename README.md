## database

**Author:** hjlarry
**Version:** 0.0.1
**Type:** extension

### Description

A database tool make it easy to query data from existing databases.

You can get different format of data, like `json`, `csv`, `yaml`, `xlsx`, `html`, `md` etc. Also support use a url to get those data.

### Usage

databaseURI support `mysql`, `postgresql`, `sqlite`
```
mysql+pymysql://root:123456@localhost:3306/test
postgresql+psycopg2://postgres:123456@localhost:5432/test
sqlite:///test.db
```

The `sql` tool is used to query data from the database.
The `query` tool is used to transform user input to a valid sql query.
The endpoint is used to get the data from a url request.

example url request:
```
curl -X POST 'https://daemon-plugin.dify.dev/o3wvwZfYFLU5iGopr5CxYmGaM5mWV7xf/sql' -H 'Content-Type: application/json' -d '{"query":"select * from test", "format": "md"}'
```
