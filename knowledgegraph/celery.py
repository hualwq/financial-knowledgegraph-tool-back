# your_project/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# 设置 Django 默认配置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'knowledgegraph.settings')

app = Celery('knowledgegraph')

# 使用默认的配置从 Django 的 settings.py 中加载
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动从 Django app 中加载任务
app.autodiscover_tasks()
