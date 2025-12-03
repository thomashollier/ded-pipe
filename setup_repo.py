#!/usr/bin/env python3
"""
Setup script to organize downloaded files into proper GitHub repository structure.

Usage:
    python setup_repo.py [zip_file]
    
    If no zip file is provided, the script will look for files in the current directory.
"""
import os
import sys
import shutil
import zipfile
from pathlib import Path
import subprocess


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text:^80}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*80}{Colors.END}\n")


def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


# File organization mapping
FILE_STRUCTURE = {
    # Root level files
    '.': [
        'README.md',
        'QUICKSTART.md',
        'PROJECT_STRUCTURE.md',
        'CONTRIBUTING.md',
        'CHANGELOG.md',
        'DOWNLOAD_GUIDE.md',
        'CLI_DOCUMENTATION.md',
        'CLI_QUICK_REFERENCE.md',
        '.gitignore',
        'LICENSE',
        'requirements.txt',
        'setup.py',
        'setup_check.py',
        'examples.py',
        'process_tst100.py',
        'ingest-cli.py',
        'config.example.json',
        'batch.example.json',
    ],
    
    # ingest_pipeline package
    'ingest_pipeline': [
        '__init__.py',
        'config.py',
        'models.py',
        'pipeline.py',
        'footage_ingest.py',
    ],
    
    # ingest_pipeline/stages
    'ingest_pipeline/stages': [
        '__init__.py',
        'base.py',
        'sony_conversion.py',
        'oiio_transform.py',
        'proxy_generation.py',
        'kitsu_integration.py',
        'file_operations.py',
    ],
    
    # GitHub workflows
    '.github/workflows': [
        'python-ci.yml',
    ],
    
    # GitHub issue templates
    '.github/ISSUE_TEMPLATE': [
        'bug_report.md',
        'feature_request.md',
    ],
    
    # GitHub PR template
    '.github': [
        'pull_request_template.md',
    ],
}


def extract_zip(zip_path, extract_to):
    """
    Extract zip file to specified directory.
    
    Args:
        zip_path: Path to zip file
        extract_to: Directory to extract to
        
    Returns:
        True if successful, False otherwise
    """
    try:
        print_info(f"Extracting {zip_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print_success(f"Extracted to {extract_to}")
        return True
    except Exception as e:
        print_error(f"Failed to extract zip: {str(e)}")
        return False


def create_directory_structure(base_path):
    """
    Create the required directory structure.
    
    Args:
        base_path: Base directory path
    """
    print_header("Creating Directory Structure")
    
    directories = [
        'ingest_pipeline',
        'ingest_pipeline/stages',
        '.github',
        '.github/workflows',
        '.github/ISSUE_TEMPLATE',
    ]
    
    base = Path(base_path)
    
    for directory in directories:
        dir_path = base / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print_success(f"Created: {directory}/")
    
    print()


def find_file(filename, search_paths):
    """
    Find a file in multiple possible locations.
    
    Args:
        filename: Name of file to find
        search_paths: List of paths to search
        
    Returns:
        Path to file if found, None otherwise
    """
    for search_path in search_paths:
        file_path = Path(search_path) / filename
        if file_path.exists():
            return file_path
    return None


def organize_files(source_dir, target_dir):
    """
    Organize files according to FILE_STRUCTURE.
    
    Args:
        source_dir: Directory containing downloaded files
        target_dir: Target repository directory
        
    Returns:
        Tuple of (success_count, missing_files)
    """
    print_header("Organizing Files")
    
    source = Path(source_dir)
    target = Path(target_dir)
    
    # Possible locations for source files
    search_paths = [
        source,
        source / 'home' / 'claude',  # If extracted with path structure
        source / 'claude',
    ]
    
    success_count = 0
    missing_files = []
    
    for target_subdir, files in FILE_STRUCTURE.items():
        for filename in files:
            # Find the source file
            source_file = find_file(filename, search_paths)
            
            if source_file:
                # Determine target location
                if target_subdir == '.':
                    target_file = target / filename
                else:
                    target_file = target / target_subdir / filename
                
                # Copy file
                try:
                    shutil.copy2(source_file, target_file)
                    print_success(f"Copied: {target_subdir}/{filename}")
                    success_count += 1
                except Exception as e:
                    print_error(f"Failed to copy {filename}: {str(e)}")
                    missing_files.append(filename)
            else:
                print_warning(f"Not found: {filename}")
                missing_files.append(filename)
    
    print()
    return success_count, missing_files


def make_scripts_executable(repo_dir):
    """
    Make Python scripts executable.
    
    Args:
        repo_dir: Repository directory
    """
    print_header("Setting File Permissions")
    
    scripts = [
        'setup_check.py',
        'examples.py',
        'process_tst100.py',
    ]
    
    repo = Path(repo_dir)
    
    for script in scripts:
        script_path = repo / script
        if script_path.exists():
            try:
                # Make executable (Unix/Mac only)
                if os.name != 'nt':  # Not Windows
                    os.chmod(script_path, 0o755)
                    print_success(f"Made executable: {script}")
                else:
                    print_info(f"Skipped (Windows): {script}")
            except Exception as e:
                print_warning(f"Could not set permissions for {script}: {str(e)}")
    
    print()


def initialize_git_repo(repo_dir, remote_url=None):
    """
    Initialize git repository and optionally add remote.
    
    Args:
        repo_dir: Repository directory
        remote_url: Optional remote URL (e.g., GitHub repo URL)
        
    Returns:
        True if successful, False otherwise
    """
    print_header("Initializing Git Repository")
    
    repo = Path(repo_dir)
    
    # Check if git is available
    try:
        result = subprocess.run(['git', '--version'], capture_output=True)
        if result.returncode != 0:
            print_error("Git is not installed or not in PATH")
            return False
    except FileNotFoundError:
        print_error("Git is not installed or not in PATH")
        return False
    
    # Initialize repo
    try:
        os.chdir(repo)
        
        # Check if already a git repo
        if (repo / '.git').exists():
            print_warning("Git repository already initialized")
        else:
            subprocess.run(['git', 'init'], check=True)
            print_success("Initialized git repository")
        
        # Add all files
        subprocess.run(['git', 'add', '.'], check=True)
        print_success("Staged all files")
        
        # Create initial commit
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():  # Only commit if there are changes
            subprocess.run(
                ['git', 'commit', '-m', 'Initial commit: Footage ingest pipeline'],
                check=True
            )
            print_success("Created initial commit")
        else:
            print_info("No changes to commit")
        
        # Add remote if provided
        if remote_url:
            # Check if remote already exists
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True
            )
            
            if result.returncode == 0:
                print_warning("Remote 'origin' already exists")
                print_info(f"Current remote: {result.stdout.decode().strip()}")
            else:
                subprocess.run(
                    ['git', 'remote', 'add', 'origin', remote_url],
                    check=True
                )
                print_success(f"Added remote: {remote_url}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print_error(f"Git command failed: {str(e)}")
        return False
    except Exception as e:
        print_error(f"Failed to initialize git: {str(e)}")
        return False


def print_summary(repo_dir, success_count, missing_files, total_files):
    """
    Print summary of operations.
    
    Args:
        repo_dir: Repository directory
        success_count: Number of files successfully copied
        missing_files: List of missing files
        total_files: Total number of expected files
    """
    print_header("Setup Summary")
    
    print(f"Repository created at: {Colors.BOLD}{repo_dir}{Colors.END}\n")
    
    print(f"Files copied: {success_count}/{total_files}")
    
    if missing_files:
        print_warning(f"\nMissing files ({len(missing_files)}):")
        for filename in missing_files:
            print(f"  - {filename}")
    else:
        print_success("\nAll files copied successfully!")
    
    print()


def print_next_steps(repo_dir, git_initialized, remote_added):
    """
    Print next steps for the user.
    
    Args:
        repo_dir: Repository directory
        git_initialized: Whether git was initialized
        remote_added: Whether remote was added
    """
    print_header("Next Steps")
    
    print(f"1. Navigate to the repository:")
    print(f"   {Colors.BOLD}cd {repo_dir}{Colors.END}\n")
    
    if git_initialized:
        print(f"2. Review the repository:")
        print(f"   {Colors.BOLD}git status{Colors.END}")
        print(f"   {Colors.BOLD}git log{Colors.END}\n")
        
        if remote_added:
            print(f"3. Push to GitHub:")
            print(f"   {Colors.BOLD}git branch -M main{Colors.END}")
            print(f"   {Colors.BOLD}git push -u origin main{Colors.END}\n")
        else:
            print(f"3. Create GitHub repository and add remote:")
            print(f"   - Go to https://github.com/new")
            print(f"   - Create repository (don't initialize with README)")
            print(f"   - Run these commands:")
            print(f"   {Colors.BOLD}git remote add origin https://github.com/USERNAME/REPO.git{Colors.END}")
            print(f"   {Colors.BOLD}git branch -M main{Colors.END}")
            print(f"   {Colors.BOLD}git push -u origin main{Colors.END}\n")
    else:
        print(f"2. Initialize git manually:")
        print(f"   {Colors.BOLD}git init{Colors.END}")
        print(f"   {Colors.BOLD}git add .{Colors.END}")
        print(f"   {Colors.BOLD}git commit -m 'Initial commit'{Colors.END}\n")
        
        print(f"3. Add remote and push:")
        print(f"   {Colors.BOLD}git remote add origin https://github.com/USERNAME/REPO.git{Colors.END}")
        print(f"   {Colors.BOLD}git branch -M main{Colors.END}")
        print(f"   {Colors.BOLD}git push -u origin main{Colors.END}\n")
    
    print(f"4. Verify setup:")
    print(f"   {Colors.BOLD}python setup_check.py{Colors.END}\n")
    
    print(f"5. Configure for your environment:")
    print(f"   - Edit {Colors.BOLD}ingest_pipeline/config.py{Colors.END}")
    print(f"   - Set tool paths")
    print(f"   - Configure shot tree paths\n")
    
    print(f"6. Test the pipeline:")
    print(f"   {Colors.BOLD}python process_tst100.py{Colors.END}\n")


def main():
    """Main function."""
    print(f"\n{Colors.BOLD}Footage Ingest Pipeline - Repository Setup{Colors.END}\n")
    
    # Parse arguments
    zip_file = None
    source_dir = None
    
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.endswith('.zip'):
            zip_file = Path(arg)
            if not zip_file.exists():
                print_error(f"Zip file not found: {zip_file}")
                sys.exit(1)
        else:
            source_dir = Path(arg)
            if not source_dir.exists():
                print_error(f"Directory not found: {source_dir}")
                sys.exit(1)
    
    # Get target directory name
    default_name = "footage-ingest-pipeline"
    print(f"Enter repository directory name [{default_name}]: ", end='')
    repo_name = input().strip() or default_name
    
    repo_dir = Path.cwd() / repo_name
    
    # Check if directory already exists
    if repo_dir.exists():
        print_warning(f"Directory already exists: {repo_dir}")
        print("Options:")
        print("  1. Use existing directory (will overwrite files)")
        print("  2. Choose a different name")
        print("  3. Exit")
        choice = input("Enter choice [1/2/3]: ").strip()
        
        if choice == '2':
            print("Enter new directory name: ", end='')
            repo_name = input().strip()
            if not repo_name:
                print_error("Invalid directory name")
                sys.exit(1)
            repo_dir = Path.cwd() / repo_name
        elif choice == '3':
            print("Exiting...")
            sys.exit(0)
        # else: continue with choice 1
    
    # Extract zip if provided
    if zip_file:
        temp_dir = Path.cwd() / 'temp_extract'
        temp_dir.mkdir(exist_ok=True)
        
        if not extract_zip(zip_file, temp_dir):
            sys.exit(1)
        
        source_dir = temp_dir
    elif not source_dir:
        # Use current directory
        source_dir = Path.cwd()
        print_info(f"Using current directory as source: {source_dir}")
    
    # Create repository structure
    repo_dir.mkdir(exist_ok=True)
    create_directory_structure(repo_dir)
    
    # Organize files
    total_files = sum(len(files) for files in FILE_STRUCTURE.values())
    success_count, missing_files = organize_files(source_dir, repo_dir)
    
    # Make scripts executable
    make_scripts_executable(repo_dir)
    
    # Print summary
    print_summary(repo_dir, success_count, missing_files, total_files)
    
    # Ask about git initialization
    print("Would you like to initialize a git repository? [Y/n]: ", end='')
    init_git = input().strip().lower() not in ['n', 'no']
    
    git_initialized = False
    remote_added = False
    
    if init_git:
        print("\nEnter GitHub repository URL (or press Enter to skip): ", end='')
        remote_url = input().strip() or None
        
        git_initialized = initialize_git_repo(repo_dir, remote_url)
        remote_added = remote_url is not None and git_initialized
    
    # Clean up temp directory if we extracted a zip
    if zip_file and source_dir.name == 'temp_extract':
        try:
            shutil.rmtree(source_dir)
        except:
            pass
    
    # Print next steps
    print_next_steps(repo_dir, git_initialized, remote_added)
    
    print_success("Repository setup complete!")
    print()


if __name__ == "__main__":
    main()
