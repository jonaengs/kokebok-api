# Kokebok API


## Running Locally

### Running Directly (with SQLite)
0. Clone this project and `cd` into it
1. Make sure Python 3.10 or higher is installed (or install pyenv and set env for this project to 3.10 or higher)
2. Install [Poetry](https://python-poetry.org/)
3. Run `poetry install` to setup a virtual environment and install dependencies
   * Note: Linters and language servers may expect the virtual environment to be located within the project directory. If you experience this issue, one solution is to run `poetry config virtualenvs.in-project true --local` before installing to have the virtual environment be installed in the project directory.
4. Activate the virtual environment either by running `poetry shell` or activating it manually
5. (First time only) set the `ENV_FILE` environment variable to `.env.dist` (using the `set` command on Windows and the `export` command on UNIX systems)
6. In the top-level 'kokebok' directory, run `python manage.py migrate` (first time only) and then run `python manage.py runserver`

### Running with Docker (with Postgres)
0. Make sure docker and docker-compose are installed
1. (First time only) Run `docker-compose build`
2. Run `docker-compose up -d`
3. (First time only) Run `docker-compose exec api python manage.py migrate --noinput`


### Other stuff
To quickly test out smaller scripts within the Django environment, run `python manage.py shell -c exec(open(<file_path>).read())`.


## Deploying to Fly.io
0. (First time) Log into fly locally by running `fly auth login`. Then run `fly launch` to configure the application. Remember to update `settings.py` and your `.env` files too!
2. Run `fly deploy`
3. (Run `fly open` to open the app in your browser)

See [this](https://fly.io/django-beats/deploying-django-to-production/#deploying-to-fly-io) article from fly.io for an introduction to deploying Django applications to their service.


## Development

### Wrong auto-import paths using VSCode/Pylance
1. Navigate to the `Python > Analysis: Extra Paths` (settings editor) or `"python.analysis.extraPaths"` (.vscode/settings.json) setting.
2. Add `./kokebok/` to the list of extra paths.
