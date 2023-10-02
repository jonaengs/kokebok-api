# Kokebok API

## Running Locally
0. Clone this project
1. Install Python 3.10 or higher (or install pyenv and set env for this project to 3.10 or higher)
2. Install [Poetry](https://python-poetry.org/)
3. Run `poetry install` to setup a virtual environment and install dependencies
   * Note: Linters and language servers may expect the virtual environment to be located within the project directory. If you experience this issue, one solution is to run `poetry config virtualenvs.in-project true --local` before installing to have the virtual environment be installed in the project directory.
4. Activate the virtual environment either by running `poetry shell` or activating it manually
5. (First time only) In `settings.py`, change the `read_env`-call to read from the `env.dist` file.
6. `cd` into the top-level kokebok directory
7. (First time only) Run `python manage.py migrate`
8. Run `python manage.py runserver`

## Deploying to Fly.io
0. (First time) Log into fly locally by running `fly auth login`. Then run `fly launch` to configure the application. Remember to update `settings.py` and your `.env` files too!
2. Run `fly deploy`
3. (Run `fly open` to open the app in your browser)

See [this](https://fly.io/django-beats/deploying-django-to-production/#deploying-to-fly-io) article from fly.io for an introduction to deploying Django applications to their service.
