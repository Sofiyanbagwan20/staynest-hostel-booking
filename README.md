# StayNest Hostel Booking

StayNest is a hostel discovery frontend with a small Flask API and database-backed
backend. The GitHub Pages preview publishes the static frontend only; backend
features such as accounts, bookings, and payments are not deployed there.

## Live preview

After the first push to `main`, the GitHub Actions workflow deploys
`hostel_booking_frontend/` to GitHub Pages. Enable Pages with **GitHub Actions**
as the build and deployment source in the repository settings if prompted.

Published site: https://sofiyanbagwan20.github.io/staynest-hostel-booking/

## Run the frontend locally

Open `hostel_booking_frontend/index.html` in a browser, or serve the folder:

```powershell
python -m http.server 8000 --directory hostel_booking_frontend
```

Then visit `http://localhost:8000`.

## Run the backend locally

1. Copy `backend/.env.example` to `backend/.env`.
2. Set a unique `JWT_SECRET` and configure the database and payment settings.
3. Install dependencies with `pip install -r backend/requirements.txt`, then
   start the Flask app with
   `python backend/app.py`.

The backend is not part of the GitHub Pages deployment. Never commit `.env`,
database files, or real credentials.

## Deploy the backend and connect GitHub Pages

GitHub Pages hosts only the static frontend. It cannot reach a backend at
`127.0.0.1`; that address refers to the visitor's own computer. To enable
accounts, saved stays, bookings, and payments online:

1. Deploy the backend using the included `render.yaml` blueprint. Review
   Render's plan and billing before confirming deployment. The blueprint uses
   a persistent disk for the SQLite database and generates a `JWT_SECRET`.
2. After deployment, copy the backend's public URL, such as
   `https://staynest-api.onrender.com`, and verify
   `https://staynest-api.onrender.com/api/health` returns an online status.
3. In the GitHub repository, open **Settings → Secrets and variables →
   Actions → Variables**, add `STAYNEST_API_BASE_URL` with the full HTTPS API
   base URL (for example `https://staynest-api.onrender.com/api`), then
   re-run the **Deploy frontend to GitHub Pages** workflow.

The Pages workflow writes that variable into a generated runtime config when
it builds the site. If the variable is missing, the frontend remains a static
demo and reports that online backend features are not configured. The backend
URL is public configuration, not a secret; do not put credentials or API
secrets in it.
