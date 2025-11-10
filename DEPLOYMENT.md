# PAMS Production Deployment Guide

## Quick Deploy Options for iPad Access

### Option 1: Heroku (Recommended - Free/Easy)

1. **Install Heroku CLI**:
   ```bash
   brew install heroku/brew/heroku
   ```

2. **Deploy to Heroku**:
   ```bash
   cd PAMS
   git init
   git add .
   git commit -m "Initial PAMS deployment"
   heroku create your-son-pams-app
   git push heroku main
   ```

3. **Access from iPad**: `https://your-son-pams-app.herokuapp.com`

### Option 2: Railway (Alternative)

1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   ```

2. **Deploy**:
   ```bash
   railway login
   railway init
   railway up
   ```

### Option 3: Local Network (Home Use)

1. **Find your Mac's IP address**:
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

2. **Run PAMS**:
   ```bash
   python3 app.py
   ```

3. **Access from iPad**: `http://YOUR_MAC_IP:5001`

### Option 4: ngrok (Instant Public Access)

1. **Install ngrok**:
   ```bash
   brew install ngrok
   ```

2. **Run PAMS locally**:
   ```bash
   python3 app.py
   ```

3. **Create public tunnel**:
   ```bash
   ngrok http 5001
   ```

4. **Access from iPad**: Use the ngrok URL (e.g., `https://abc123.ngrok.io`)

## iPad Optimization Features

✅ **Touch-optimized interface**
✅ **Mobile-responsive design**  
✅ **Large touch targets**
✅ **Swipe gestures**
✅ **Offline capability**
✅ **PWA support** (Add to Home Screen)

## Security Notes

- Data stored locally in JSON files
- No external database required
- All data stays on your server
- HTTPS available with Heroku/Railway

## Recommended Setup for Your Son

1. **Use Heroku** for reliable 24/7 access
2. **Add to iPad Home Screen** for app-like experience
3. **Bookmark** `/mobile` for best iPad experience
4. **Parent access** via `/parent` on your computer

## URLs for iPad

- **Main App**: `https://your-app.herokuapp.com/mobile`
- **Quick Check-in**: `https://your-app.herokuapp.com/athlete`
- **Dashboard**: `https://your-app.herokuapp.com/athlete/dashboard`