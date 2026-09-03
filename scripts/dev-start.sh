#!/bin/bash

# PsychSync Development Server Manager
# Automatically handles process cleanup and server startup

set -e

echo "🚀 Starting PsychSync Development Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to kill existing processes
kill_existing_processes() {
    echo -e "${YELLOW}🧹 Cleaning up existing processes...${NC}"

    # Kill any existing uvicorn processes on port 8000
    pkill -f "uvicorn.*8000" 2>/dev/null || true
    pkill -f "python.*app.main:app" 2>/dev/null || true
    pkill -f "python.*minimal_app:app" 2>/dev/null || true

    # Kill any existing frontend processes on ports 5173 and 5174
    pkill -f "npm.*dev.*5173" 2>/dev/null || true
    pkill -f "npm.*dev.*5174" 2>/dev/null || true
    pkill -f "vite.*5173" 2>/dev/null || true
    pkill -f "vite.*5174" 2>/dev/null || true

    # Wait for processes to fully terminate
    sleep 3

    # Kill any stubborn processes on specific ports
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:5173 | xargs kill -9 2>/dev/null || true
    lsof -ti:5174 | xargs kill -9 2>/dev/null || true

    echo -e "${GREEN}✅ Process cleanup complete${NC}"
}

# Function to check if ports are available
check_ports() {
    local port=8000
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ Port $port is still in use${NC}"
        return 1
    fi

    local port=5173
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ Port $port is still in use${NC}"
        return 1
    fi

    echo -e "${GREEN}✅ Ports are available${NC}"
    return 0
}

# Function to start backend
start_backend() {
    echo -e "${BLUE}🔧 Starting backend server...${NC}"
    cd /Users/sheriftito/Downloads/psychsync

    # Activate virtual environment if it exists
    if [ -d ".venv" ]; then
        source .venv/bin/activate
        echo -e "${GREEN}✅ Virtual environment activated${NC}"
    fi

    # Start minimal_app in background
    nohup uvicorn minimal_app:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > .backend_pid

    echo -e "${GREEN}✅ Backend starting (PID: $BACKEND_PID)${NC}"

    # Wait a moment for backend to start
    sleep 5
}

# Function to start frontend
start_frontend() {
    echo -e "${BLUE}🎨 Starting frontend server...${NC}"
    cd /Users/sheriftito/Downloads/psychsync/frontend

    # Start frontend in background
    nohup npm run dev -- --port 5173 > frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../.frontend_pid

    echo -e "${GREEN}✅ Frontend starting (PID: $FRONTEND_PID)${NC}"

    # Wait a moment for frontend to start
    sleep 5
}

# Function to verify servers are running
verify_servers() {
    echo -e "${BLUE}🔍 Verifying servers are running...${NC}"

    # Check backend
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is responding${NC}"
    else
        echo -e "${RED}❌ Backend is not responding${NC}"
        return 1
    fi

    # Check frontend
    if curl -s http://localhost:5173 >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend is responding${NC}"
    else
        echo -e "${RED}❌ Frontend is not responding${NC}"
        return 1
    fi

    return 0
}

# Function to show status
show_status() {
    echo -e "${BLUE}📊 Server Status:${NC}"

    if [ -f ".backend_pid" ]; then
        BACKEND_PID=$(cat .backend_pid)
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Backend running (PID: $BACKEND_PID)${NC}"
        else
            echo -e "${RED}❌ Backend not running${NC}"
        fi
    else
        echo -e "${RED}❌ Backend PID file not found${NC}"
    fi

    if [ -f ".frontend_pid" ]; then
        FRONTEND_PID=$(cat .frontend_pid)
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Frontend running (PID: $FRONTEND_PID)${NC}"
        else
            echo -e "${RED}❌ Frontend not running${NC}"
        fi
    else
        echo -e "${RED}❌ Frontend PID file not found${NC}"
    fi

    echo ""
    echo -e "${BLUE}🌐 Access URLs:${NC}"
    echo -e "Frontend: ${GREEN}http://localhost:5173${NC}"
    echo -e "Backend API: ${GREEN}http://localhost:8000${NC}"
    echo -e "API Docs: ${GREEN}http://localhost:8000/docs${NC}"
}

# Function to stop servers
stop_servers() {
    echo -e "${YELLOW}🛑 Stopping servers...${NC}"

    if [ -f ".backend_pid" ]; then
        BACKEND_PID=$(cat .backend_pid)
        kill $BACKEND_PID 2>/dev/null || true
        rm .backend_pid 2>/dev/null || true
        echo -e "${GREEN}✅ Backend stopped${NC}"
    fi

    if [ -f ".frontend_pid" ]; then
        FRONTEND_PID=$(cat .frontend_pid)
        kill $FRONTEND_PID 2>/dev/null || true
        rm .frontend_pid 2>/dev/null || true
        echo -e "${GREEN}✅ Frontend stopped${NC}"
    fi

    # Final cleanup
    kill_existing_processes
}

# Main execution
main() {
    case "${1:-start}" in
        "start")
            kill_existing_processes
            if ! check_ports; then
                echo -e "${RED}❌ Ports not available, exiting${NC}"
                exit 1
            fi
            start_backend
            start_frontend
            sleep 3
            if verify_servers; then
                show_status
                echo -e "${GREEN}🎉 PsychSync development environment is ready!${NC}"
                echo -e "${BLUE}💡 Use '$0 status' to check status, '$0 stop' to stop servers${NC}"
            else
                echo -e "${RED}❌ Failed to start servers properly${NC}"
                stop_servers
                exit 1
            fi
            ;;
        "stop")
            stop_servers
            ;;
        "restart")
            stop_servers
            sleep 2
            main start
            ;;
        "status")
            show_status
            ;;
        "logs")
            echo -e "${BLUE}📋 Backend logs:${NC}"
            tail -20 backend.log 2>/dev/null || echo "No backend logs found"
            echo ""
            echo -e "${BLUE}📋 Frontend logs:${NC}"
            tail -20 frontend.log 2>/dev/null || echo "No frontend logs found"
            ;;
        *)
            echo -e "${BLUE}PsychSync Development Server Manager${NC}"
            echo ""
            echo "Usage: $0 {start|stop|restart|status|logs}"
            echo ""
            echo "Commands:"
            echo "  start   - Start all development servers"
            echo "  stop    - Stop all development servers"
            echo "  restart - Restart all development servers"
            echo "  status  - Show server status"
            echo "  logs    - Show recent server logs"
            echo ""
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
