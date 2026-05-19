import io
import sys
import asyncio

# Redirect stdout to a string buffer
old_stdout = sys.stdout
sys.stdout = io.StringIO()

try:
    from check_postgres_users import seed_supabase_direct
    asyncio.run(seed_supabase_direct())
except Exception as e:
    print(f"\nCRITICAL EXCEPTION IN RUNNER: {e}")
finally:
    # Get the logs and restore stdout
    logs = sys.stdout.getvalue()
    sys.stdout = old_stdout
    
    # Save the logs to a file in the workspace
    with open("seeding_execution.log", "w") as f:
        f.write(logs)
    print("Logs written to seeding_execution.log")
