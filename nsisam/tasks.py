from os import listdir, remove
from os.path import join
from celery import Celery, Task, registry
from restfulie import Restfulie

celery =  Celery()
celery.config_from_object('celeryconfig')

@celery.task
def clean_files(path, sam_host, sam_port, sam_user, sam_password):
    print 'Cleaning the files...'
    sam = Restfulie.at("http://%s:%s/" % (sam_host, sam_port))
    sam = sam.auth(sam_user, sam_password).as_('application/json')
    for entry in listdir(path):
        if sam.get(key=entry).code == '404':
            remove(join(path, entry))
    print 'Done.'
