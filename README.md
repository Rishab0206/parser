# 🏦 Bank Statement Intelligence Engine (v2.0)
### Production-Ready Bank Statement Parser & Financial Intelligence Dashboard

A production-grade banking parser engine built with **FastAPI**, **React 18 + Vite**, **PyMuPDF**, and **SQLAlchemy**. Designed for automated business loan underwriting, turnover extraction, Average Bank Balance (ABB) calculation, EMI detection, and bounce analysis.

---

## 📂 Project Structure

```text
bank-statement-intelligence-github/
├── backend/                  # FastAPI Python backend engine
│   ├── app/                  # Application core, models, parsers, services, API routers
│   ├── alembic/              # Database migration scripts
│   ├── tests/                # 26 automated unit test suites
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile            # Container deployment specification
│   └── alembic.ini
├── frontend/                 # React + TypeScript + Tailwind CSS UI
│   ├── src/                  # Components, Pages, API clients, Utils
│   ├── public/               # Static assets
│   ├── index.html
│   ├── package.json          # Node dependencies
│   ├── vite.config.ts        # Vite build & proxy config
│   └── tailwind.config.js
├── render.yaml               # 🚀 Render 1-Click Blueprint specification
├── .gitignore                # Production ignore rules (no node_modules or credentials)
├── .env.example              # Sample environment configuration
└── README.md                 # Deployment & setup guide
```

---

## 🚀 How to Push to GitHub (Step-by-Step)

### Step 1: Create a New Repository on GitHub
1. Open [GitHub](https://github.com) and sign in.
2. Click the **+** icon in the top right → **New repository**.
3. Name it: `bank-statement-intelligence` (or any name you prefer).
4. Choose **Public** or **Private**.
5. Do **NOT** check "Add a README" or ".gitignore" (these are already configured in this folder).
6. Click **Create repository**.

### Step 2: Push this folder from your PC
Open PowerShell in this folder (`E:\bank-statement-intelligence-github`):

```powershell
cd "E:\bank-statement-intelligence-github"

# 1. Initialize git
git init

# 2. Add all files
git add .

# 3. Commit
git commit -m "feat: complete banking intelligence parser engine with customer history and new reset flow"

# 4. Set main branch
git branch -M main

# 5. Connect to your GitHub repo (replace with your actual GitHub repo URL)
git remote add origin https://github.com/YOUR_USERNAME/bank-statement-intelligence.git

# 6. Push code to GitHub
git push -u origin main
```

---

## ☁️ How to Deploy on Render.com (Make it Live for Employees)

### Method 1: Automated 1-Click Deployment (Recommended)
This repository includes a `render.yaml` Blueprint file that configures both the backend and frontend automatically.

1. Go to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** → Select **Blueprint**.
3. Connect your GitHub account and select your `bank-statement-intelligence` repository.
4. Render will automatically detect `render.yaml` and show:
   * **`bank-statement-api`** (Python Web Service)
   * **`bank-statement-dashboard`** (React Static Site)
5. Click **Apply**.
6. Render will build and deploy both services! Once finished, you will receive a public HTTPS link (e.g. `https://bank-statement-dashboard.onrender.com`).

---

### Method 2: Manual Setup on Render

#### A. Deploy Backend Web Service
1. In Render Dashboard, click **New +** → **Web Service**.
2. Connect your GitHub repo.
3. Configure the following:
   * **Name**: `bank-statement-api`
   * **Root Directory**: `backend`
   * **Environment**: `Python 3`
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   * **Plan**: `Free`
4. Under **Environment Variables**, add:
   * `ENVIRONMENT`: `production`
   * `STORAGE_PATH`: `./uploads`
   * `DATABASE_URL`: `sqlite:///./bank_intelligence.db`
   * `ENCRYPTION_KEY`: `45071192004245607314794888115900`
   * `CORS_ORIGINS`: `*`
5. Click **Create Web Service**. Note down the live backend URL (e.g. `https://bank-statement-api.onrender.com`).

#### B. Deploy Frontend Static Site
1. In Render Dashboard, click **New +** → **Static Site**.
2. Connect the same GitHub repo.
3. Configure the following:
   * **Name**: `bank-statement-dashboard`
   * **Root Directory**: `frontend`
   * **Build Command**: `npm install && npm run build`
   * **Publish Directory**: `dist`
4. Under **Environment Variables**, add:
   * `VITE_API_BASE_URL`: Paste your backend URL from Step A (e.g. `https://bank-statement-api.onrender.com`).
5. Under **Redirects/Rewrites**:
   * Add a Rewrite rule:
     * **Type**: `Rewrite`
     * **Source**: `/*`
     * **Destination**: `/index.html`
6. Click **Create Static Site**.

---

## 👥 Sharing with Other Employees
Once deployed on Render:
1. Copy the live frontend link (e.g. `https://bank-statement-dashboard.onrender.com`).
2. Share this link with your team members/employees.
3. Employees can access it from any browser, laptop, or mobile without installing Python or Node.
4. All features are live:
   * **Statement Upload**: PDF, scanned PDF, Excel, and CSV with auto-detection of bank and customer name.
   * **New Customer / Reset**: Clean slate for new applications while preserving old ones.
   * **Customer Banking History**: Persistent customer records showing Turnover, ABB, EMIs, and ACH/ECS bounces with 1-click customer switching.
   * **Export to Underwriting**: Download structured financial payloads for underwriting.

