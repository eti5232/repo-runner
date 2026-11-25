import subprocess

print(subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout)
