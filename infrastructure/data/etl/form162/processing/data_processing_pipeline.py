import subprocess
import sys
import time
import os

def run_script(script_path):
    print(f"\nStarting {script_path}...")
    try:
        script_name = os.path.basename(script_path)
        script_dir = os.path.dirname(script_path)
        pipeline_dir = os.path.dirname(script_dir)  # This will be data_processing directory

        # Run from data_processing directory
        result = subprocess.run([sys.executable, os.path.join("scripts", script_name)],
                              check=True,
                              cwd=pipeline_dir)  # Set working directory to data_processing
        if result.returncode == 0:
            print(f"Successfully completed {script_path}")
            return True
        else:
            print(f"Error running {script_path}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"Error executing {script_path}: {e}")
        return False
    except FileNotFoundError:
        print(f"Script not found: {script_path}")
        return False

def main():
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

    scripts = [
        os.path.join(CURRENT_DIR, "scripts", "stage_1.py"),
        os.path.join(CURRENT_DIR, "scripts", "stage_2.py")
    ]

    start_time = time.time()

    for script in scripts:
        success = run_script(script)
        if not success:
            print(f"\nPipeline failed at {script}")
            sys.exit(1)

    end_time = time.time()
    print(f"\nAll scripts completed successfully!")
    print(f"Total execution time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()