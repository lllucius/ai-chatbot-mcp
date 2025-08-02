#!/bin/bash

# AI Chatbot Frontend Setup Script
# This script helps you get the React frontend up and running quickly

echo "🚀 AI Chatbot Frontend Setup"
echo "=============================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ and try again."
    exit 1
fi

echo "✅ Node.js found: $(node --version)"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm and try again."
    exit 1
fi

echo "✅ npm found: $(npm --version)"

# Navigate to frontend directory
if [ ! -d "frontend" ]; then
    echo "❌ Frontend directory not found. Please run this script from the ai-chatbot-mcp root directory."
    exit 1
fi

cd frontend

echo "📦 Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies. Please check your internet connection and try again."
    exit 1
fi

echo "✅ Dependencies installed successfully!"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating environment configuration..."
    cat > .env << EOF
# AI Chatbot Frontend Configuration
REACT_APP_API_URL=http://localhost:8000

# Optional: Enable additional logging in development
REACT_APP_DEBUG=true
EOF
    echo "✅ Created .env file with default configuration"
else
    echo "✅ Environment file already exists"
fi

echo ""
echo "🎉 Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Make sure the backend API is running on http://localhost:8000"
echo "2. Start the frontend development server:"
echo "   cd frontend && npm start"
echo ""
echo "3. Open your browser to http://localhost:3000"
echo ""
echo "📚 For detailed documentation, see frontend/FRONTEND_README.md"
echo ""
echo "Default admin credentials (if using the provided backend):"
echo "   Username: admin"
echo "   Password: Admin123!"
echo ""
echo "Happy coding! 🚀"