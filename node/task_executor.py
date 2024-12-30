import subprocess
from api_client import APIClient

class TaskExecutor:
    def __init__(self):
        self.api_client = APIClient()

    def ensure_docker_installed(self):
        """
        Ensure Docker is installed on the node.
        If not, attempt to install Docker automatically.
        """
        try:
            subprocess.run(
                "docker --version",
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            print("[TASK EXECUTOR] Docker is already installed.")
        except subprocess.CalledProcessError:
            print("[TASK EXECUTOR] Docker not found. Installing Docker...")
            try:
                subprocess.run(
                    """
                    curl -fsSL https://get.docker.com | sh &&
                    sudo usermod -aG docker $USER &&
                    sudo systemctl start docker
                    """,
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True
                )
                print("[TASK EXECUTOR] Docker installation completed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"[ERROR] Docker installation failed: {e.stderr}")
                raise Exception("Docker installation failed. Please check the logs and try again.")

    def execute_task(self, task):
        task_id = task['id']
        container_spec = task.get('container_spec', {})
        image = container_spec.get('image', "")
        command = container_spec.get('command', "")
        env = container_spec.get('env', {})
        credentials = container_spec.get('docker_credentials', {})  # Handle Docker credentials

        print(f"[TASK EXECUTOR] Executing Task {task_id} with image '{image}'")

        try:
            # Step 1: Docker Login (if credentials are provided)
            if credentials:
                print(f"[TASK EXECUTOR] Logging into Docker registry: {credentials.get('registry', 'Docker Hub')}")
                docker_login_command = (
                    f"docker login {credentials.get('registry', '')} "
                    f"-u {credentials.get('username')} "
                    f"-p {credentials.get('password')}"
                )
                subprocess.run(
                    docker_login_command,
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True
                )

            # Step 2: Pull the Docker image
            print(f"[TASK EXECUTOR] Pulling Docker image: {image}")
            subprocess.run(
                f"docker pull {image}",
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )

            # Step 3: Run the container with the specified command and environment variables
            docker_command = (
                f"docker run --rm "
                f"{' '.join([f'-e {k}={v}' for k, v in env.items()])} "
                f"{image} {command}"
            )

            print(f"[TASK EXECUTOR] Running Docker command: {docker_command}")
            process = subprocess.run(
                docker_command,
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )

            result = {"output": process.stdout.strip(), "error": process.stderr.strip()}
            status = "success"

        except subprocess.CalledProcessError as e:
            result = {"output": e.stdout.strip(), "error": e.stderr.strip()}
            status = "failed"
            print(f"[TASK EXECUTOR] Docker command failed: {e.stderr.strip()}")
        except Exception as e:
            result = {"error": str(e)}
            status = "failed"
            print(f"[TASK EXECUTOR] Unexpected error: {str(e)}")

        finally:
            # Step 4: Docker Logout (if login was performed)
            if credentials:
                print(f"[TASK EXECUTOR] Logging out from Docker registry.")
                subprocess.run(
                    f"docker logout {credentials.get('registry', '')}",
                    shell=True,
                    check=False,  # Don't fail the task if logout fails
                    capture_output=True,
                    text=True
                )

        # Step 5: Submit the result to the hub
        result['status'] = status
        self.api_client.submit_result(task_id, result)

        print(f"[TASK EXECUTOR] Task {task_id} completed with status '{status}'. Result sent.")
