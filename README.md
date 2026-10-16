# Lafaya

## Setup

- Clone the repository:

```bash
# Windows: use HTTPS
git clone https://github.com/vidoushi08/Lafaya.git

# macOS / Linux: use SSH
git clone git@github.com:vidoushi08/Lafaya.git

cd Lafaya
```

- Create a virtual environment:

```bash
# Windows
python -m venv venv

# macOS / Linux
python3 -m venv venv
```

- Activate the virtual environment:

```bash
# Windows (Command Prompt)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate
```

- Install the dependencies:

```bash
pip install -r requirements.txt
```

## Usage

- Apply database migrations:

```bash
python manage.py migrate
```

- Create a Django admin superuser:

```bash
python manage.py createsuperuser
```

- Run the server:

```bash
python manage.py runserver
```

- Open `http://127.0.0.1:8000/` in your browser.

> [NOTE]
> The Django admin panel is available at `http://127.0.0.1:8000/admin/`.

### Existing database created before the custom customer account model

If this project database already has `auth_user` and the built-in admin
migrations recorded, but does not have `authentication_user`, back up
`db.sqlite3` before migrating. Then run:

```bash
python manage.py shell -c 'from django.db import connection; connection.cursor().execute("DELETE FROM django_migrations WHERE app = %s", ["admin"])'
python manage.py migrate authentication 0001_initial
python manage.py migrate admin 0003_logentry_add_action_flag_choices --fake
python manage.py migrate
```

This preserves existing accounts and admin history while moving the project
to the custom customer account model. New databases only need the standard
`python manage.py migrate` command.
