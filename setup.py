#!/usr/bin/env python3
"""
Document Processing Platform Setup Script
This script helps set up the development environment for the document processing platform.
"""

import os
import sys
import subprocess
import shutil
import time
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ {command}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running: {command}")
        print(f"Error: {e.stderr}")
        return None

def check_requirements():
    """Check if required software is installed"""
    print("🔍 Checking system requirements...")
    
    requirements = {
        "python": "python --version",
        "node": "node --version",
        "npm": "npm --version",
        "docker": "docker --version",
        "docker-compose": "docker-compose --version"
    }
    
    missing = []
    for tool, command in requirements.items():
        if run_command(command) is None:
            missing.append(tool)
    
    if missing:
        print(f"❌ Missing required software: {', '.join(missing)}")
        print("Please install the missing software and try again.")
        return False
    
    print("✅ All requirements met!")
    return True

def setup_backend():
    """Set up the backend environment"""
    print("\n🐍 Setting up backend...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found!")
        return False
    
    # Create virtual environment
    if not (backend_dir / "venv").exists():
        print("Creating virtual environment...")
        run_command("python -m venv venv", cwd=backend_dir)
    
    # Install dependencies
    print("Installing Python dependencies...")
    pip_cmd = "venv/bin/pip" if os.name != "nt" else "venv\\Scripts\\pip"
    run_command(f"{pip_cmd} install -r requirements.txt", cwd=backend_dir)
    
    # Download spaCy model
    print("Downloading spaCy model...")
    python_cmd = "venv/bin/python" if os.name != "nt" else "venv\\Scripts\\python"
    run_command(f"{python_cmd} -m spacy download en_core_web_sm", cwd=backend_dir)
    
    # Create necessary directories
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("ml_models/cache", exist_ok=True)
    
    print("✅ Backend setup complete!")
    return True

def setup_frontend():
    """Set up the frontend environment"""
    print("\n⚛️ Setting up frontend...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found!")
        return False
    
    # Install dependencies
    print("Installing Node.js dependencies...")
    run_command("npm install", cwd=frontend_dir)
    
    print("✅ Frontend setup complete!")
    return True

def setup_database():
    """Set up the database"""
    print("\n🗄️ Setting up database...")
    
    # Start database services
    print("Starting database services...")
    run_command("docker-compose up -d postgres redis")
    
    # Wait for services to be ready
    print("Waiting for services to be ready...")
    time.sleep(10)
    
    print("✅ Database setup complete!")
    return True

def create_env_file():
    """Create environment file from example"""
    print("\n📝 Creating environment file...")
    
    if not Path(".env").exists() and Path(".env.example").exists():
        shutil.copy(".env.example", ".env")
        print("✅ Environment file created from example!")
        print("⚠️  Please review and update the .env file with your configuration.")
    else:
        print("ℹ️  Environment file already exists or example not found.")
    
    return True

def run_tests():
    """Run tests to verify setup"""
    print("\n🧪 Running tests...")
    
    # Backend tests
    backend_dir = Path("backend")
    if backend_dir.exists():
        python_cmd = "venv/bin/python" if os.name != "nt" else "venv\\Scripts\\python"
        run_command(f"{python_cmd} -m pytest tests/ -v", cwd=backend_dir)
    
    # Frontend tests
    frontend_dir = Path("frontend")
    if frontend_dir.exists():
        run_command("npm test -- --watchAll=false", cwd=frontend_dir)
    
    print("✅ Tests completed!")
    return True

def main():
    """Main setup function"""
    print("🚀 Document Processing Platform Setup")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Create environment file
    create_env_file()
    
    # Setup backend
    if not setup_backend():
        sys.exit(1)
    
    # Setup frontend
    if not setup_frontend():
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        sys.exit(1)
    
    # Run tests
    run_tests()
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Review and update the .env file with your configuration")
    print("2. Start the application with: docker-compose up")
    print("3. Access the application at: http://localhost:3000")
    print("4. Access the API docs at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
