#!/usr/bin/env python3

from app import create_app
import logging

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=True)
