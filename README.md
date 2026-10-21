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

### Seaside catalogue images

Superadmins can upload images when managing Seaside venues, packages, and
optional services. Uploaded files are stored under the project's local `media/`
directory; SQLite stores the file paths, not the image contents. Back up the
`media/` directory alongside `db.sqlite3`. Uploaded images can be served by the
development server while `DEBUG=True`; production deployment needs an
appropriate media-file storage and serving configuration.
