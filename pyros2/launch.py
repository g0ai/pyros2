import subprocess

def get_conda_python_path(conda_env_name):
    try:
        # For Linux/Mac, use 'which python'; for Windows, use 'where python'
        cmd = f"conda init bash && conda activate {conda_env_name} && which python" 
        python_path = subprocess.check_output(cmd, shell=True, executable='/bin/zsh').decode().strip()
        return python_path
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        return None


class Launcher():
    def __init__(self, root=".", env=None, env_name=None):
        self._root = root
        self._processes = []
        if env is None:
            self._python = "python"
        elif env == "conda":
            self._python = f"/Users/ibrahim/opt/anaconda3/envs/{env_name}/bin/python" # get_conda_python_path(env_name)
            # print(self._python)

    def add(self, file):
        self._processes.append(subprocess.Popen([self._python, file], cwd=self._root))

    def run(self, cmd):
        self._processes.append(subprocess.Popen(cmd, cwd=self._root))

    def launch(file, root="."):
        # subprocess.run(['python', file])
        p = subprocess.Popen(['python', file], cwd=root)
        exit_codes = p.wait()


    def wait(self):
        exit_codes = [p.wait() for p in self._processes]