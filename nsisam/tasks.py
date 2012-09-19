from os import listdir, remove
from celery import Celery, Task
from redis import Redis

celery =  Celery()
celery.config_from_object('celeryconfig')

class CleanFiles(Task):

	def run(self, path, redis_config):
		for server in redis_config:
			redis = Redis(*server)
			for entry in listdir(path):
				if not redis.get(entry):
					os.remove(entry)

