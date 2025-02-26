from server import celery, app

if __name__ == '__main__':
    with app.app_context():
        celery.worker_main(['worker', '--loglevel=info'])
