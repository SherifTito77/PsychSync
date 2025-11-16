#!/bin/bash

# PsychSync Localhost Development Stop Script
# This script stops all development services

echo "🛑 Stopping PsychSync Localhost Development Environment..."

docker-compose down

echo "✅ All services stopped!"
echo ""
echo "💾 To remove all data (including database), run:"
echo "   docker-compose down -v"
echo ""
echo "🧹 To remove all containers and images, run:"
echo "   docker system prune -a"