#!/usr/bin/env python3

# Copyright © 2025 Hugo Dünger -  ZKM | Zentrum für Kunst und Medien Karlsruhe
# Lizenziert unter der MIT-Lizenz

import os
import sys
import subprocess
import pathlib
import shutil
import time
import stat

# --- Configuration ---
PI_USER = "dietpi"
PI_HOST = "192.168.42.1"
PI_PORT = 22
HUGO_DIR = "hugo-page"
REMOTE_PATH = "/var/www/public"
# --- End Configuration ---

# Path to shared virtual environment
VENV_PATH = pathlib.Path(__file__).parent / ".venv"
PYTHON_BIN = VENV_PATH / "bin" / "python"

def ensure_venv():
    """Ensure .venv exists, Paramiko is installed, and script is running inside venv."""
    if not VENV_PATH.exists():
        print("Creating virtual environment...")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_PATH)])

    pip_bin = VENV_PATH / "bin" / "pip"
    result = subprocess.run([str(pip_bin), "show", "paramiko"], stdout=subprocess.DEVNULL)
    if result.returncode != 0:
        print("Installing Paramiko in virtual environment...")
        subprocess.check_call([str(pip_bin), "install", "paramiko"])

    # Re-run inside venv if not already
    if sys.executable != str(PYTHON_BIN):
        print("Re-running script inside virtual environment...")
        os.execv(str(PYTHON_BIN), [str(PYTHON_BIN)] + sys.argv)

# Ensure venv and paramiko are ready before importing
ensure_venv()

import paramiko

def build_hugo():
    """Build Hugo site in hugo-page/public."""
    hugo_path = os.path.join(os.getcwd(), HUGO_DIR)
    public_path = os.path.join(hugo_path, "public")

    if not os.path.isdir(hugo_path):
        print(f"Hugo directory '{HUGO_DIR}' not found.")
        sys.exit(1)

    if os.path.exists(public_path):
        shutil.rmtree(public_path)

    print("Building Hugo site...")
    result = subprocess.run(["hugo", "--minify"], cwd=hugo_path)
    if result.returncode != 0:
        print("Hugo build failed.")
        sys.exit(1)

    print("Hugo build complete.")
    return public_path

def connect_ssh():
    """Connect to Pi via SSH."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_HOST, port=PI_PORT, username=PI_USER)
    return ssh

def run_remote(ssh, command, stop_on_error=True):
    """Run command on remote Pi."""
    stdin, stdout, stderr = ssh.exec_command(command)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if err and stop_on_error:
        print(f"Remote command error:\n{err}")
        ssh.close()
        sys.exit(1)
    return out

def upload_if_needed(sftp, local_path, remote_path):
    try:
        remote_attr = sftp.stat(remote_path)
        local_size = os.path.getsize(local_path)
        remote_size = remote_attr.st_size

        if local_size == remote_size:
            return False
    except FileNotFoundError:
        pass

    sftp.put(local_path, remote_path)
    return True


def list_remote_files(sftp, remote_dir):
    """Recursively list remote files."""
    files = []
    try:
        for entry in sftp.listdir_attr(remote_dir):
            rpath = os.path.join(remote_dir, entry.filename).replace("\\", "/")
            if stat.S_ISDIR(entry.st_mode):
                files.extend(list_remote_files(sftp, rpath))
            else:
                files.append(rpath)
    except FileNotFoundError:
        pass
    return files

def sync_directory(sftp, local_dir, remote_dir):
    """Sync local_dir to remote_dir over SFTP with deletion of extra remote files."""
    try:
        sftp.stat(remote_dir)
    except FileNotFoundError:
        sftp.mkdir(remote_dir)

    local_files = {}
    for root, _, files in os.walk(local_dir):
        rel_dir = os.path.relpath(root, local_dir)
        for f in files:
            local_path = os.path.join(root, f)
            remote_path = os.path.join(remote_dir, rel_dir, f).replace("\\", "/")
            local_files[remote_path] = local_path

    remote_files = list_remote_files(sftp, remote_dir)

    # Delete remote files not present locally
    for rf in remote_files:
        if rf not in local_files:
            try:
                sftp.remove(rf)
                print(f"Deleted remote file: {rf}")
            except Exception as e:
                print(f"Could not delete {rf}: {e}")

    # Upload files
    for remote_path, local_path in local_files.items():
        remote_folder = os.path.dirname(remote_path)
        # ensure folder exists
        parts = remote_folder.split("/")
        path_so_far = ""
        for p in parts:
            if not p:
                continue
            path_so_far = path_so_far + "/" + p
            try:
                sftp.stat(path_so_far)
            except FileNotFoundError:
                sftp.mkdir(path_so_far)
        # upload file
        try:
            if upload_if_needed(sftp, local_path, remote_path):
                print(f"Uploaded: {remote_path}")

        except Exception as e:
            print(f"Upload failed for {local_path}: {e}")

def deploy():
    """Main deployment routine."""
    public_path = build_hugo()
    ssh = connect_ssh()

    # Switch Pi to read-write
    run_remote(ssh, "sudo mount -o remount,rw /")

    # Prepare remote directory
    run_remote(ssh, f"sudo mkdir -p {REMOTE_PATH}")
    run_remote(ssh, f"sudo chown -R {PI_USER}:{PI_USER} {REMOTE_PATH}")

    # Sync files via SFTP
    for attempt in range(3):
        try:
            with ssh.open_sftp() as sftp:
                sync_directory(sftp, public_path, REMOTE_PATH)
            break
        except paramiko.SSHException:
            print("SFTP subsystem not ready, retrying...")
            time.sleep(2)
    else:
        print("Error: SFTP subsystem not available.")
        ssh.close()
        sys.exit(1)

    # Final permissions and remount read-only
    run_remote(ssh, f"sudo chown -R www-data:www-data {REMOTE_PATH}")
    run_remote(ssh, f"sudo chmod -R 755 {REMOTE_PATH}")
    run_remote(ssh, "sudo mount -o remount,ro /")

    ssh.close()
    print("Deployment complete.")

if __name__ == "__main__":
    deploy()
    input("Press Enter to exit...")
