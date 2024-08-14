
from zmq import ssh
import paramiko

# SSH Connection Details
ssh_host = "192.168.100.125"
ssh_port = 22
ssh_user = "ibrahim"
ssh_password = "password"

# Remote and Local Ports
# remote_port = 5555  # Port where the publisher is bound
# local_port = 5555   # Local port to forward

# Setup SSH Tunnel
def create_ssh_tunnel(sock, ):
    # ssh = paramiko.SSHClient()
    # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # ssh.connect(ssh_host, port=ssh_port, username=ssh_user, password=ssh_password)

    # tunnel = ssh.get_transport().open_channel(
    #     'direct-tcpip', 
    #     ('localhost', remote_port), 
    #     ('localhost', local_port)
    # )

    tunnel = ssh.tunnel_connection(self.s, self.conn, ssh_server, password = "password")

    return tunnel