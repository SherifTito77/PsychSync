# PsychSync Development Scripts

## 🚀 Quick Start (No More Manual Server Management!)

### Option 1: Simple Development Script (Recommended)
```bash
./dev.sh
```
This automatically:
- Kills any existing processes on ports 8000, 5173, 5174
- Starts the backend (minimal_app) on port 8000
- Starts the frontend on port 5173
- Verifies both servers are working
- Provides URLs for easy access

### Option 2: NPM Script
```bash
npm run dev
```
Does the same as `./dev.sh` but uses npm

### Option 3: Full-Featured Development Script
```bash
./scripts/dev-start.sh          # Start servers
./scripts/dev-start.sh status   # Check status
./scripts/dev-start.sh stop     # Stop servers
./scripts/dev-start.sh logs     # View logs
./scripts/dev-start.sh restart  # Restart servers
```

### Option 4: NPM Full-Featured
```bash
npm run dev-full    # Start servers
npm run dev-stop    # Stop servers
```

## 🛑 Stopping Servers

### Quick Stop
```bash
pkill -f uvicorn && pkill -f 'npm.*dev'
```

### Clean Stop
```bash
npm run dev-stop
# or
./scripts/dev-start.sh stop
```

## 🔧 What These Scripts Solve

**Before:** You had to manually:
1. Close existing servers
2. Remember the uvicorn command: `uvicorn app.main:app --reload`
3. Manage multiple terminal windows
4. Handle port conflicts manually
5. Restart when things broke

**After:** Just run:
```bash
./dev.sh
```

That's it! The scripts handle:
- ✅ Automatic process cleanup
- ✅ Port conflict resolution
- ✅ Virtual environment activation
- ✅ Server health verification
- ✅ Log management
- ✅ PID tracking

## 📁 File Locations

- **Main Script**: `/Users/sheriftito/Downloads/psychsync/dev.sh`
- **Full Script**: `/Users/sheriftito/Downloads/psychsync/scripts/dev-start.sh`
- **Package Scripts**: Added to `package.json` as `dev`, `dev-full`, `dev-stop`

## 🌐 Access URLs

Once the script completes, you can access:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🔍 Troubleshooting

If something goes wrong:

1. **Check what's running**:
   ```bash
   ./scripts/dev-start.sh status
   ```

2. **View logs**:
   ```bash
   ./scripts/dev-start.sh logs
   ```

3. **Force restart**:
   ```bash
   ./dev.sh
   ```

4. **Manual cleanup (if needed)**:
   ```bash
   pkill -f uvicorn
   pkill -f 'npm.*dev'
   lsof -ti:8000 | xargs kill -9
   lsof -ti:5173 | xargs kill -9
   ```

## 💡 Pro Tips

1. **Single Command Development**: Add this to your shell aliases:
   ```bash
   alias psychsync='./dev.sh'
   ```

2. **Automatic Restart**: The scripts detect existing processes and clean them automatically, so you can just run `./dev.sh` again to restart.

3. **Background Mode**: Servers run in background, so you can close your terminal after startup.

4. **Log Files**: Check `.backend.log` and `.frontend.log` for detailed error information.

**That's it! No more manual uvicorn commands needed!** 🎉