web: gunicorn course_website.wsgi --log-file - 
#or works good with external database
web: python manage.py migrate && gunicorn course_website.wsgi