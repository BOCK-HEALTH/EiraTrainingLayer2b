# ⚡ BOCK Scraper - Quick Start (5 Minutes)

**Get scraping in 5 minutes!**

---

## 1️⃣ Install Python (If Not Installed)

Download from [python.org](https://www.python.org/downloads/) - Version 3.8 or higher

✅ Check "Add Python to PATH" during installation

---

## 2️⃣ Open Terminal in Project Folder

**Windows:** Right-click folder → "Open in Terminal"  
**Mac/Linux:** `cd /path/to/bock-scraper`

---

## 3️⃣ Create Virtual Environment

```bash
python -m venv web_venv
```

---

## 4️⃣ Activate Virtual Environment

**Windows:**
```bash
web_venv\Scripts\activate
```

**Mac/Linux:**
```bash
source web_venv/bin/activate
```

You should see `(web_venv)` in your prompt.

---

## 5️⃣ Install Dependencies (One Command)

```bash
pip install -r requirements.txt && pip install -r ec2_files/requirements.txt && pip install -r summary/bocksummarizer-main/requirements.txt
```

**Wait 5-10 minutes** for installation to complete.

---

## 6️⃣ Start the Server

```bash
python web_server.py
```

**You should see:**
```
BOCK SCRAPER - WEB INTERFACE
Open your browser and go to: http://localhost:5000
```

---

## 7️⃣ Open Browser

Go to: **http://localhost:5000**

---

## 🎯 First Scraping Job

1. **URL:** `https://www.bbc.com/news`
2. **Max Articles:** `5`
3. Click **"Start Scraping"**
4. Watch the magic happen! 🚀

**Output:** Check `scraping_output/session_XXXXX/` folder

---

## ✅ That's It!

You now have:
- ✅ Web scraper running locally
- ✅ Beautiful web interface
- ✅ AI summarization ready (will download models on first use)

---

## 🆘 Having Issues?

### "Python not found"
→ Install Python and add to PATH

### "Port 5000 already in use"
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID [NUMBER] /F
```

### "Module not found"
→ Make sure virtual environment is activated (you should see `(web_venv)`)

---

## 📚 Next Steps

- Read [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions
- Check [FEATURES.md](FEATURES.md) for all capabilities
- See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details

---

**🎉 Happy Scraping!**

