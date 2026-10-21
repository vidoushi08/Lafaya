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

  ### Booking approval and demo payments

  Booking requests appear in the superadmin site's **Bookings** queue. Add the
  approved amount to the booking's payment record, then use the booking action to
  approve or reject it. Customers can mark an approved booking as paid using the
  credit/debit card demo from **Payments** in their account area. This demo does
  not collect card details or charge a real card.
  After a successful demo payment, the customer receives a receipt email with
  the booking reference, event date, and amount. Card data is never included in
  that email or sent to the server. If email delivery fails, the customer can
  retry sending the receipt from the payment page.

  Individual amounts can be adjusted for each pending booking in the admin.
  Payment approval and email delivery are separate: if an email cannot be sent,
  the saved booking decision is retained and the admin reports the delivery
  failure.

## Usage

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

## Sharing catalogue data (prices, packages, venues, services)

Git only shares code. The data entered through the admin (prices, price bases,
packages, venues, services) lives in each person's local `db.sqlite3`, so a
merge does not bring a teammate's data. Share it with fixtures: JSON files that
are committed to the repository and loaded into the database.

Never export users, payments, or booking requests. They contain personal data.

### On the laptop that owns the data

1. Enter the prices and catalogue items in the admin at
   `http://127.0.0.1:8000/admin/`.
2. Export the approved catalogue models to their app fixture files:

```bash
python manage.py export_catalog_fixtures
```

   This exports Birthday, Car Events, Conference, and Seaside catalogues. To
   export only selected apps, list them after the command, for example:
   `python manage.py export_catalog_fixtures seaside conference`.
3. Commit and push the fixtures along with any uploaded catalogue images:

```bash
git add birthday/fixtures car_events/fixtures conference/fixtures seaside/fixtures media
git commit -m "Update catalogue fixtures and images"
git push
```

4. Whenever prices or items change and the defaults should be updated for
   everyone, repeat steps 2 and 3.

### On the laptop receiving the data

1. Merge or pull the owner's branch:

```bash
git fetch origin
git merge origin/<owner-branch>
```

2. Apply the database migrations, then load the fixtures:

```bash
python manage.py migrate
python manage.py load_catalog
```

   `load_catalog` loads the Birthday, Car Events, Conference, and Seaside
   fixtures in one step.

3. Open the site or the admin to check that the prices appear.

> [WARNING]
> `loaddata` overwrites rows that have the same primary key, so it replaces any
> prices already edited in your local database. Run it on a fresh or development
> database, not on a database whose prices were changed on purpose afterwards.

Catalogue images uploaded through the admin are stored under
`media/<app>/catalog/`, and those files are tracked by git so teammates see the
same images after pulling. Other media, such as profile pictures, stays local.

### Seaside catalogue images

Superadmins can upload images when managing Seaside venues, packages, and
optional services. Uploaded files are stored under the project's local `media/`
directory; SQLite stores the file paths, not the image contents. Back up the
`media/` directory alongside `db.sqlite3`. Uploaded images can be served by the
development server while `DEBUG=True`; production deployment needs an
appropriate media-file storage and serving configuration.
