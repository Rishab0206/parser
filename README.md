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

## ☁️ How to Deploy on Render.com (`banking-parser`)

### ⚠️ Why your repo is not showing in Render (and how to fix it):
If you search on Render and cannot find your repository:
1. **GitHub Permission Restriction**: On Render, click **"New +"** → **"Web Service"**. At the bottom of the repo list, click **"Configure Render on GitHub"** (or go to [GitHub App Permissions for Render](https://github.com/settings/installations)). Ensure **`Rishab0206/parser`** (or your new **`banking-parser`** repo) is selected under "Repository access".
2. **Repository Name**: On GitHub, your repo is named **`parser`** (`https://github.com/Rishab0206/parser`). Search for `parser` in the Render search box!
3. **Want a separate repository named `banking-parser`?**:
   - Create a new repo on GitHub named `banking-parser`.
   - Double click `PUSH_TO_BANKING_PARSER.bat` and select Option 2 to enter `https://github.com/Rishab0206/banking-parser.git`.

---

### 🚀 Active Render Profile: 1-Click Unified Web Service (Recommended)
This repository contains a production **Active Render Profile** configured as **`banking-parser`**.
It packages both the **React 18 Dashboard** and **FastAPI Python Parser Engine** into **one single unified service**.

#### Why this unified profile is best:
* **Single Live URL** (e.g. `https://banking-parser.onrender.com`) for both the frontend UI and backend API.
* **Zero CORS errors** and zero broken links.
* **100% Free Tier Compatible**: Uses only 1 Render free service instead of 2.

#### Deployment Steps:
1. In [Render Dashboard](https://dashboard.render.com), click **New +** → **Web Service**.
2. Select your repository (**`parser`** or **`banking-parser`**).
3. Render will auto-detect the root **`Dockerfile`**.
4. Set:
   * **Name**: `banking-parser`
   * **Region**: Oregon or Frankfurt
   * **Instance Type**: `Free`
5. Click **Create Web Service**.
6. Render will build both the frontend and backend, run all OCR tools, and give you your live URL!

---

### 🛠️ Alternative Method: Deploy via Blueprint (`render.yaml`)
1. In Render Dashboard, click **New +** → **Blueprint**.
2. Connect your repo and select branch `main`.
3. Render reads `render.yaml` and deploys the **`banking-parser`** profile automatically.
4. Click **Apply**.
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

