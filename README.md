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
