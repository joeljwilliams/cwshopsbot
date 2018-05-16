#!/usr/bin/env python3
import os
import requests

TOKEN = os.getenv('BOT_TOKEN')
APP_ENV = os.getenv('APP_ENV')

DB_USER = os.getenv('DATABASE_USER')
DB_PASS = os.getenv('DATABASE_PASSWORD')
DB_HOST = os.getenv('DATABASE_SERVICE_NAME')
DB_NAME = os.getenv('DATABASE_NAME')

RESULT_SIZE = int(os.getenv('RESULT_SIZE', 30))

SHOP_API = os.getenv('SHOPS_API_ENDPOINT', 'https://cw.krasovsky.me/api/shops')  # thanks https://t.me/kraso

UPDATE_INTERVAL = int(os.getenv('SHOPS_UPDATE_INTERVAL', 90))

if APP_ENV == 'PROD_OPENSHIFT':
    LOGLEVEL = 'INFO'
    os_namespace = os.getenv("OPENSHIFT_BUILD_NAMESPACE")
    os_app_name, build = os.getenv("OPENSHIFT_BUILD_NAME").rsplit('-', 1)
    DB_PARAMS = {'provider': 'postgres',
                 'user': DB_USER,
                 'password': DB_PASS,
                 'host': DB_HOST,
                 'database': DB_NAME}
    with open("/var/run/secrets/kubernetes.io/serviceaccount/token") as f:
        os_api_token = f.read()
    os_api_url = "https://openshift.default.svc.cluster.local/oapi/v1/"
    os_api_crt = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
    headers = {'Authorization': 'Bearer {}'.format(os_api_token)}
    r = requests.get(f"{os_api_url}namespaces/{os_namespace}/routes/{os_app_name}", headers=headers, verify=os_api_crt)
    WEBHOOK_URL = r.json()["spec"]["host"]
    WEBHOOK_PORT = int(os.getenv("{}_SERVICE_PORT_WEB".format(os_app_name.upper().replace('-', '_'))))
elif APP_ENV == 'PROD_HEROKU':
    LOGLEVEL = 'INFO'
    DB_PARAMS = {'provider': 'postgres',
                 'dsn': os.getenv('DATABASE_URL')}

    WEBHOOK_PORT = int(os.getenv('PORT'))
    WEBHOOK_URL = 'cw-shops-bot.herokuapp.com'
else:
    LOGLEVEL = 'DEBUG'
