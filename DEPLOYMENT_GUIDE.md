# Complete Deployment Guide
## Intelligent Academic Asset Recovery and Management System
**Sanskriti University &bull; Academic Asset Cell**

This project is fully configured for production deployment across multiple environments. Choose the deployment option that fits your needs:

---

## 🌐 Option 1: Free 1-Click Cloud Deployment on Render (Recommended)

Render provides free hosting for Python web applications. The project includes `render.yaml` and `Procfile` pre-configured.

### Steps:
1. **Push your code to GitHub:**
   - Create a free GitHub repository (e.g. `academic-asset-system`).
   - Push the contents of `c:\Users\bandi\OneDrive\Desktop\academic_asset_system` to your repository.

2. **Deploy on Render (Free Tier):**
   - Go to [https://render.com](https://render.com) and sign up / log in with your GitHub account.
   - Click **New +** ➔ **Web Service**.
   - Select your GitHub repository.
   - Configure the settings (or Render will automatically detect `render.yaml`):
     - **Name:** `sanskriti-academic-assets`
     - **Environment:** `Python 3`
     - **Region:** Any (e.g., `Oregon (US West)` or `Singapore`)
     - **Branch:** `main` (or `master`)
     - **Build Command:** `pip install -r requirements.txt && python seed_data.py`
     - **Start Command:** `gunicorn wsgi:app --workers 2 --bind 0.0.0.0:$PORT`
     - **Instance Type:** `Free`
   - Click **Deploy Web Service**.

3. **Access Your Live Portal:**
   - In 2–3 minutes, Render will provision your URL:  
     `https://sanskriti-academic-assets.onrender.com`

---

## 🐳 Option 2: Docker Container Deployment (Any Cloud Server, VPS, AWS, GCP)

The project includes a production-ready `Dockerfile` and `docker-compose.yml`.

### Single-Command Run:
```bash
docker compose up -d --build
```

### Or using Standard Docker CLI:
```bash
# 1. Build the production image
docker build -t sanskriti-academic-assets .

# 2. Run the container
docker run -d -p 5000:5000 --name sanskriti_portal sanskriti-academic-assets
```
Your containerized app will be live at `http://localhost:5000`.

---

## ⚡ Option 3: Immediate Live Internet Tunnel (Zero Setup - Perfect for College Presentation)

If you need an **instant public HTTPS link** to show your professors tomorrow on your smartphone, tablet, or presentation screen without signing up for cloud hosting, you can expose your local server securely:

### Method A: Free Cloudflare Tunnel (No Account Required)
1. Download `cloudflared` executable from [Cloudflare Releases](https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe).
2. Start your app in one terminal:
   ```powershell
   python app.py
   ```
3. In another terminal, run:
   ```powershell
   cloudflared tunnel --url http://localhost:5000
   ```
4. Cloudflare will instantly output a public URL like:  
   `https://random-subdomain.trycloudflare.com`  
   You can open this URL on **any device anywhere in the world**!

### Method B: Same College Wi-Fi Direct Access (No Internet Tunnel Needed)
Because `app.py` is configured with `host='0.0.0.0'`, anyone connected to the same college Wi-Fi can directly access your project by typing your laptop's Wi-Fi IP address in their mobile browser:
👉 **`http://10.166.5.211:5000`**

---

## ☁️ Option 4: PythonAnywhere Deployment

1. Register for a free account at [https://www.pythonanywhere.com](https://www.pythonanywhere.com).
2. Go to the **Files** tab and upload the project zip.
3. Open a **Bash Console** and run:
   ```bash
   pip install -r requirements.txt
   python seed_data.py
   ```
4. In the **Web** tab, configure a new **Manual Flask** web app pointing to `app.py`.
5. Reload your web app to visit: `https://yourusername.pythonanywhere.com`.
