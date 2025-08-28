#!/usr/bin/env python3
"""
Setup script for On-Device Agentic Battery Optimization System
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def create_directories():
    """Create necessary directories"""
    directories = [
        'models',
        'logs',
        'config',
        'dashboard/templates',
        'dashboard/static'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    return True

def check_system_requirements():
    """Check system requirements and capabilities"""
    print("🔍 Checking system requirements...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 8):
        print(f"❌ Python 3.8+ required, found {python_version.major}.{python_version.minor}")
        return False
    else:
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check platform
    system = platform.system()
    print(f"✅ Platform: {system}")
    
    # Check available modules
    required_modules = ['psutil', 'numpy', 'sklearn', 'flask', 'cv2']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} available")
        except ImportError:
            missing_modules.append(module)
            print(f"⚠️  {module} not found")
    
    if missing_modules:
        print(f"📦 Missing modules will be installed: {', '.join(missing_modules)}")
    
    return True

def setup_configuration():
    """Setup default configuration if needed"""
    config_file = Path('config/default.json')
    if not config_file.exists():
        print("⚠️  Configuration file not found, it should be created automatically")
    else:
        print("✅ Configuration file exists")

def check_permissions():
    """Check if the system has necessary permissions"""
    print("🔒 Checking system permissions...")
    
    system = platform.system().lower()
    
    if system == 'windows':
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if is_admin:
                print("✅ Running with administrator privileges")
            else:
                print("⚠️  Not running as administrator - some optimizations may not work")
                print("   Consider running as administrator for full functionality")
        except Exception:
            print("⚠️  Could not check administrator status")
    
    elif system == 'linux':
        if os.geteuid() == 0:
            print("✅ Running with root privileges")
        else:
            print("⚠️  Not running as root - some optimizations may require sudo")
            print("   System will work but some features may be limited")
    
    else:
        print(f"⚠️  Unsupported platform: {system}")
        print("   System may work with limited functionality")

def run_basic_test():
    """Run a basic functionality test"""
    print("🧪 Running basic functionality test...")
    
    try:
        # Test imports
        from core.monitoring import SystemMonitor
        from core.reasoning import BatteryOptimizationAgent
        from core.actions import OptimizationActuator
        from core.agent_controller import AgentController
        
        print("✅ Core modules import successfully")
        
        # Test basic functionality
        monitor = SystemMonitor(update_interval=5.0)
        metrics = monitor.collect_metrics()
        print(f"✅ Monitoring works - Battery: {metrics.battery_percent:.1f}%")
        
        # Test agent
        agent = BatteryOptimizationAgent()
        print("✅ Agent initialization works")
        
        # Test actuator
        actuator = OptimizationActuator()
        print("✅ Actuator initialization works")
        
        print("✅ Basic functionality test passed")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🔋 On-Device Agentic Battery Optimization System - Setup")
    print("=" * 60)
    
    # Check system requirements
    if not check_system_requirements():
        print("❌ System requirements not met")
        return False
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        return False
    
    # Setup configuration
    setup_configuration()
    
    # Check permissions
    check_permissions()
    
    # Run basic test
    if not run_basic_test():
        print("❌ Basic functionality test failed")
        print("   You may need to install additional system packages")
        return False
    
    print("\n" + "=" * 60)
    print("✅ Setup completed successfully!")
    print("\n🚀 You can now run the system:")
    print("   python test_system.py      # Full demonstration")
    print("   python main.py --dashboard # Agent with web dashboard")
    print("   python demo_app/video_player.py  # Demo video player")
    print("\n📊 Web dashboard will be available at: http://localhost:5000")
    print("📖 See README.md for detailed usage instructions")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
