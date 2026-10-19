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

- Configure email by filling in the `.env` file in the project root. Set
  `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, and `DEFAULT_FROM_EMAIL` to your Gmail
  address, Google App Password, and sender address. The App Password is a secret:
  keep it in `.env` and do not commit or share it.

  Gmail SMTP uses `smtp.gmail.com` on port `587` with TLS. The project loads these
  values from `.env`; it uses Django's console email backend until both the Gmail
  address and App Password are set.

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

### Seaside catalogue images

Superadmins can upload images when managing Seaside venues, packages, and
optional services. Uploaded files are stored under the project's local `media/`
directory; SQLite stores the file paths, not the image contents. Back up the
`media/` directory alongside `db.sqlite3`. Uploaded images can be served by the
development server while `DEBUG=True`; production deployment needs an
appropriate media-file storage and serving configuration.
