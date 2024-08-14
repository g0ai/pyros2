import paramiko

# SSH Connection Details
ssh_host = "192.168.100.125"
ssh_port = 22
ssh_user = "ibrahim"
ssh_password = "password"


# Setup SSH Tunnel
def create_ssh_tunnel(remote_port=8768, local_port=8768):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ssh_host, port=ssh_port, username=ssh_user, password=ssh_password)

    tunnel = ssh.get_transport().open_channel(
        'direct-tcpip', 
        ('localhost', remote_port), 
        ('localhost', local_port)
    )

    return tunnel