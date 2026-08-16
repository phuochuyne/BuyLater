# buylater full-stack application

This package combines the verified Backend Generator package unchanged with the
current complete responsive Frontend Generator pages. Each compiled page carries
its visual system locally and does not require a frontend CDN at runtime.

## Run locally

1. Create and activate a Python virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and replace its example values.
4. Apply `database/schema.sql` to MySQL.
5. Run `pytest -q`.
6. Start the complete application:
   `flask --app 'fullstack:create_app()' run --debug`
7. Open a screen route listed in `frontend-package-manifest.json`.


## Local setup note

The package was assembled successfully, but Zorentia's temporary runtime check
reported:

- `frontend_application_boot_failed`

Your completed files are included. Follow the setup steps above, then paste any
local error into Goat Helper for guided debugging.

