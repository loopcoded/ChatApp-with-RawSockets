# run_gui.py - Simple launcher for the GUI client
import os
import sys

# Add the current directory to the path so imports work correctly
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

try:
    from gui_client import main
    main()
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required files are in the correct locations:")
    print("- gui_client.py (this directory)")
    print("- backend/rsa_utils.py")
    print("- backend/server_public.pem (generated when server runs)")
except Exception as e:
    print(f"Error running GUI client: {e}")
    input("Press Enter to exit...")