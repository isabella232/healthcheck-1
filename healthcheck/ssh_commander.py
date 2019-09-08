import logging

from concurrent.futures import ThreadPoolExecutor, wait
from subprocess import Popen, PIPE


class SshCommander(object):
    """
    SSH-Commander class.
    """

    def __init__(self, _username, _hostnames, _keyfile):
        """
        :param _username: The ssh username to log in.
        :param _hostnames: A list with hostnames to log in.
        :param _keyfile: The path to the ssh identity file.
        """
        self.username = _username
        self.hostnames = _hostnames
        self.keyfile = _keyfile
        self.cache = {}

    def get_log_file_path(self, _node_nr=0):
        cmd = 'df -h /var/opt/redislabs/log'
        return self._exec_on_node(cmd, _node_nr)

    def get_tmp_file_path(self, _node_nr=0):
        cmd = 'df -h /tmp'
        return self._exec_on_node(cmd, _node_nr)

    def get_rladmin_info(self, _node_nr=0):
        cmd = f'sudo /opt/redislabs/bin/rladmin info node {_node_nr + 1}'
        return self._exec_on_node(cmd, _node_nr)

    def get_swappiness(self, _node_nr=0):
        cmd = 'grep swap /etc/sysctl.conf || echo -n inactive'
        return self._exec_on_node(cmd, _node_nr)

    def get_transparent_hugepage(self, _node_nr=0):
        cmd = 'cat /sys/kernel/mm/transparent_hugepage/enabled'
        return self._exec_on_node(cmd, _node_nr)

    def run_rladmin_status(self, _node_nr=0):
        cmd = 'sudo /opt/redislabs/bin/rladmin status'
        return self._exec_on_node(cmd, _node_nr)

    def run_rlcheck(self, _node_nr=0):
        cmd = '/opt/redislabs/bin/rlcheck'
        return self._exec_on_node(cmd, _node_nr)

    def run_cnm_ctl_status(self, _node_nr=0):
        cmd = 'sudo /opt/redislabs/bin/cnm_ctl status'
        return self._exec_on_node(cmd, _node_nr)

    def run_supervisorctl_status(self, _node_nr=0):
        cmd = 'sudo /opt/redislabs/bin/supervisorctl status'
        return self._exec_on_node(cmd, _node_nr)

    def find_errors_in_syslog(self, _node_nr=0):
        cmd = 'sudo grep error /var/log/syslog || echo ""'
        return self._exec_on_node(cmd, _node_nr)

    def find_errors_in_install_log(self, _node_nr=0):
        cmd = 'grep error /var/opt/redislabs/log/install.log || echo ""'
        return self._exec_on_node(cmd, _node_nr)

    def _exec_on_ip(self, _cmd, _ip):
        """
        Execute a SSH command on an IP address.

        :param _cmd: The command to execute.
        :param _ip: The IP address of the remote machine.
        :return: The result.
        :raise Exception: If an error occurred.
        """
        return self._exec_ssh(self.username, _ip, self.keyfile, _cmd)

    def _exec_on_all_ips(self, _cmd):
        """
        Execute a SSH command on all IP addresses.

        :param _cmd: The command to execute.
        :return: The results.
        :raise Exception: If an error occurred.
        """
        number_of_nodes = len(self.hostnames)
        with ThreadPoolExecutor(max_workers=number_of_nodes) as e:
            futures = [e.submit(self._exec_on_ip, _cmd, ip) for ip in self.hostnames]
            done, undone = wait(futures)
            assert not undone
            return [d.result() for d in done]

    def _exec_on_node(self, _cmd, _node_nr):
        """
        Execute a SSH remote command an a node.

        :param _cmd: The command to execute.
        :param _node_nr: The index in the array of the configured IP addresses.
        :return: The response.
        :raise Excpetion: If an error occurred.
        """
        return self._exec_ssh(self.username, self.hostnames[_node_nr], self.keyfile, _cmd)

    def _exec_on_all_nodes(self, _cmd, _number_of_nodes):
        """
        Execute a SSH command on all nodes.

        :param _cmd: The command to execute.
        :param _number_of_nodes: The amount of nodes.
        :return: The results.
        :raise Excpetion: If an error occurred.
        """
        with ThreadPoolExecutor(max_workers=_number_of_nodes) as e:
            futures = [e.submit(self._exec_on_node, _cmd, node_nr) for node_nr in range(0, _number_of_nodes)]
            done, undone = wait(futures)
            assert not undone
            return [d.result() for d in done]

    def _exec_ssh(self, _user, _host, _keyfile, _cmd):
        """
        Execute a SSH command.

        :param _user: The remote username.
        :param _host: The remote machine.
        :param _keyfile: The private keyfile.
        :param _cmd: The command to execute.
        :return: The response.
        :raise Exception: If an error occurred.
        """
        if _host in self.cache and _cmd in self.cache[_host]:
            return self.cache[_host]

        cmd = ' '.join(['ssh', '-i {}'.format(_keyfile), '{}@{}'.format(_user, _host), '-C', _cmd])
        rsp = SshCommander.exec_cmd(cmd)
        if _host not in self.cache:
            self.cache[_host] = {}
        self.cache[_host][cmd] = rsp

        return rsp

    @staticmethod
    def exec_cmd(_args):
        """
        Execute a SSH command string.

        :param _args: The command string.
        :return: The response.
        :raise Exception: If an error occurred.
        """
        logging.debug(_args)
        proc = Popen(_args, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
        proc.wait()
        if proc.returncode == 0:
            rsp = proc.stdout.read().decode('utf-8')
            return rsp
        else:
            rsp = proc.stderr.read().decode('utf-8')
            raise Exception(f'error during ssh remote execution (return code {proc.returncode}): {rsp}')

    @staticmethod
    def exec_func_on_all_nodes(_func, _number_of_nodes):
        """
        Execute a function on all noces.

        :param _func: The function to execeute.
        :param _number_of_nodes: The number of nodes.
        :return: The results.
        :raise Exception: If an error occurred.
        """
        with ThreadPoolExecutor(max_workers=_number_of_nodes) as e:
            futures = [e.submit(_func, node_nr) for node_nr in range(0, _number_of_nodes)]
            done, undone = wait(futures)
            assert not undone
            return [d.result() for d in done]
