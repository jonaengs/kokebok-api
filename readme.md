# Kokebok API


## Running Locally

### Running Directly (with SQLite)
0. Clone this project and `cd` into it
1. Make sure Python 3.10 or higher is installed (or install pyenv and set env for this project to 3.10 or higher)
2. Install [Poetry](https://python-poetry.org/)
3. Run `poetry install` to setup a virtual environment and install dependencies
   * Note: Linters and language servers may expect the virtual environment to be located within the project directory. If you experience this issue, one solution is to run `poetry config virtualenvs.in-project true --local` before installing to have the virtual environment be installed in the project directory.
4. Activate the virtual environment either by running `poetry shell` or activating it manually
5. (First time only) copy the `.example.env.dev` file into a file called `.env.dev`. This is the file you will use to configure your local setup.
6. In the top-level directory, run `DEBUG=true python kokebok/manage.py migrate` (first time only) and then run `DEBUG=true python kokebok/manage.py runserver`

### Running with Docker (with Postgres)
0. Make sure docker and docker-compose are installed
1. (First time only) Run `docker-compose build`
2. Run `docker-compose up -d`
3. (First time only) Run `docker-compose exec api python manage.py migrate --noinput`


### Other stuff
To quickly test out smaller scripts within the Django environment, run `python manage.py shell -c exec(open(<file_path>).read())`.

There's a script called `populate.py` inside the recipes app which can be ran through the django shell to quickly generate some test data.

## Deploying
Make sure that you've configured the app correctly before deploying. The simplest way to do this is to use a `.env` file to store all configuration settings. The file is already in `.gitignore` rules. The `.env.dev` file contains example values for all env variables used, though the values there are meant for local development and are not suited for use in a production environment.

Make sure you know what you are doing and are aware of the potential consequences before setting `STRICT_SSL=True`. Note that certain TLDs like `.dev` are "HTTP-only", and are already preloaded into the HSTS lists of modern web browsers.


### Deploying to Fly.io
0. (First time) Log into fly locally by running `fly auth login`. Then run `fly launch` to configure the application. Remember to update `settings.py` and your `.env` files too!
2. Run `fly deploy`
3. (Run `fly open` to open the app in your browser)

See [this](https://fly.io/django-beats/deploying-django-to-production/#deploying-to-fly-io) article from fly.io for an introduction to deploying Django applications to their service.


### Media files in production
The application is set up to host media files on S3 (or some other S3-compatible service). Once you have an S3 bucket and access keys (see (here)[https://testdriven.io/blog/storing-django-static-and-media-files-on-amazon-s3/] for a guide), the following variables must be set (either as environment variables or in the `.env` file):
```
AWS_STORAGE_BUCKET_NAME
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_S3_REGION_NAME
```


### OCR using Google Cloud
In your Google Cloud Console, create a project for use with this app. Then add/enable the "Cloud Vision API" for your project. Create a Service Account and grant it the role of "Vertex AI User". Generate keys for that user and place the key/credentials file somewhere in this repository. Extract (into the `.env` file for example) the data from credentials file into the following environment variables:
```
GOOGLE_PROJECT_ID
GOOGLE_PRIVATE_KEY_ID
GOOGLE_PRIVATE_KEY
GOOGLE_CLIENT_EMAIL
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_X509_CERT_URL
```

## Development

### Wrong auto-import paths using VSCode/Pylance
1. Navigate to the `Python > Analysis: Extra Paths` (settings editor) or `"python.analysis.extraPaths"` (.vscode/settings.json) setting.
2. Add `./kokebok/` to the list of extra paths.
