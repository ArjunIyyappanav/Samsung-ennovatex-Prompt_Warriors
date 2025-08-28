#!/usr/bin/env python3
"""
Main entry point for the On-Device Agentic Battery Optimization System
"""

import sys
import time
import logging
import argparse
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from core.agent_controller import AgentController
from core.monitoring import SystemMonitor
from core.reasoning import BatteryOptimizationAgent
from core.actions import OptimizationActuator
from dashboard.web_dashboard import WebDashboard
from utils.logger import setup_logging

def main():
    """Main function to start the battery optimization system"""
    parser = argparse.ArgumentParser(description='On-Device Battery Optimization System')
    parser.add_argument('--config', type=str, default='config/default.json',
                      help='Configuration file path')
    parser.add_argument('--dashboard', action='store_true',
                      help='Start web dashboard')
    parser.add_argument('--demo', action='store_true',
                      help='Run demo mode with sample application')
    parser.add_argument('--log-level', type=str, default='INFO',
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                      help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    logger = logging.getLogger(__name__)
    
    logger.info("🔋 Starting On-Device Agentic Battery Optimization System")
    
    try:
        # Initialize the agentic controller
        controller = AgentController(config_path=args.config)
        
        # Start web dashboard if requested
        if args.dashboard:
            dashboard = WebDashboard(controller)
            dashboard.start(threaded=True)
            logger.info("📊 Web dashboard started at http://localhost:5000")
        
        # Run demo mode if requested
        if args.demo:
            from demo_app.video_player import VideoPlayerDemo
            demo_app = VideoPlayerDemo()
            controller.register_target_application(demo_app)
            logger.info("🎥 Demo video player registered as target application")
        
        # Start the main optimization loop
        logger.info("🤖 Starting agentic optimization loop...")
        controller.start()
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Stopping battery optimization system...")
            controller.stop()
            
    except Exception as e:
        logger.error(f"❌ Error starting system: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
