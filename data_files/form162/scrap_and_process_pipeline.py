# scrap_and_process_pipeline.py
import subprocess
import sys
import time
import os

def run_script(script_path):
    print(f"\nStarting {script_path}...")
    try:
        # Get the parent directory of the script to run
        script_dir = os.path.dirname(script_path)
        parent_dir = os.path.dirname(script_dir)  # This will be data_scrapping or data_processing
        
        # Run the script from its parent directory
        result = subprocess.run([sys.executable, script_path], check=True,
                              cwd=parent_dir)  # Set working directory to parent
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
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    pipeline_scripts = [
        os.path.join(BASE_DIR, "data_scrapping", "data_scrapping_pipeline.py"),
        os.path.join(BASE_DIR, "data_processing", "data_processing_pipeline.py")
    ]
    
    start_time = time.time()
    print("Starting main pipeline execution...")
    
    for pipeline in pipeline_scripts:
        print(f"\n{'='*50}")
        print(f"Executing pipeline: {pipeline}")
        print(f"{'='*50}")
        
        success = run_script(pipeline)
        if not success:
            print(f"\nMain pipeline failed at {pipeline}")
            sys.exit(1)
    
    end_time = time.time()
    print(f"\n{'='*50}")
    print("All pipelines completed successfully!")
    print(f"Total execution time: {end_time - start_time:.2f} seconds")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()