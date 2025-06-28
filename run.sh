#!/bin/bash

# SmartAla Navigation App Runner
echo "🚀 Starting SmartAla Navigation Application..."
echo "📍 Application will be available at: http://127.0.0.1:5002"
echo "🎤 Voice assistant ready for blind navigation"
echo ""

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development

# Run the Flask application without reloader to avoid watchdog issues
python -c "
import app
if __name__ == '__main__':
    app.app.run(debug=False, host='127.0.0.1', port=5002, use_reloader=False)
" 