import re

from healthcheck.check_suites.base_suite import BaseCheckSuite
from healthcheck.ssh_commander import SshCommander


class SystemChecks(BaseCheckSuite):
    """Check System Health"""

    def check_os_version(self, *_args, **_kwargs):
        number_of_nodes = self.api.get_number_of_values('nodes')
        os_versions = self.api.get_values('nodes', 'os_version')

        kwargs = {f'node{i + 1}': os_versions[i] for i in range(0, number_of_nodes)}
        return "get os version of all nodes", None, kwargs

    def check_log_file_path(self, *_args, **_kwargs):
        number_of_nodes = self.api.get_number_of_values('nodes')
        log_file_paths = []
        for log_file_path in SshCommander.exec_func_on_all_nodes(self.ssh.get_log_file_path, number_of_nodes):
            match = re.match(r'^([\w+/]+)\s+.*$', log_file_path.split('\n')[1], re.DOTALL)
            log_file_paths.append( match.group(1))

        result = any(['/dev/root' not in log_file_path for log_file_path in log_file_paths])
        kwargs = {f'node{i + 1}': log_file_paths[i] for i in range(0, number_of_nodes)}
        return "check if log file path is on root filesystem", result, kwargs

    def check_tmp_file_path(self, *_args, **_kwargs):
        number_of_nodes = self.api.get_number_of_values('nodes')
        tmp_file_paths = []
        for tmp_file_path in SshCommander.exec_func_on_all_nodes(self.ssh.get_tmp_file_path, number_of_nodes):
            match = re.match(r'^([\w+/]+)\s+.*$', tmp_file_path.split('\n')[1], re.DOTALL)
            tmp_file_paths.append(match.group(1))

        result = any(['/dev/root' not in tmp_file_path for tmp_file_path in tmp_file_paths])
        kwargs = {f'node{i + 1}': tmp_file_paths[i] for i in range(0, number_of_nodes)}
        return "check if tmp file path is on root filesystem", result, kwargs

    def check_swappiness(self, *_args, **_kwargs):
        number_of_nodes = self.api.get_number_of_values('nodes')
        swappinesses = SshCommander.exec_func_on_all_nodes(self.ssh.get_swappiness, number_of_nodes)

        kwargs = {f'node{i + 1}': swappinesses[i] for i in range(0, number_of_nodes)}
        return "get swap setting of all nodes", None, kwargs

    def check_transparent_hugepage(self, *_args, **_kwargs):
        number_of_nodes = self.api.get_number_of_values('nodes')
        transparent_hugepages = SshCommander.exec_func_on_all_nodes(self.ssh.get_transparent_hugepage, number_of_nodes)

        kwargs = {f'node{i + 1}': transparent_hugepages[i] for i in range(0, number_of_nodes)}
        return "get THP setting of all nodes", None, kwargs

    def check_rladmin_status(self, *_args, **_kwargs):
        status = self.ssh.run_rladmin_status()
        found = re.findall(r'^((?!OK).)*$', status.strip(), re.MULTILINE)
        not_ok = len(found)

        return "check rladmin status", not not_ok, {'not OK': not_ok}

    def check_rlcheck_result(self, *_args, **_kwargs):
        check = self.ssh.run_rlcheck()
        found = re.findall(r'^((?!error).)*$', check.strip(), re.MULTILINE)
        errors = len(found)

        return "check rlcheck status", not errors, {'rlcheck errors': errors}

    def check_cnm_ctl_status(self, *_args, **_kwargs):
        status = self.ssh.run_cnm_ctl_status()
        found = re.findall(r'^((?!RUNNING).)*$', status.strip(), re.MULTILINE)
        not_running = len(found)

        result = not_running == 0
        return "check cnm_ctl status", result, {'not RUNNING': not_running}

    def check_supervisorctl_status(self, *_args, **_kwargs):
        status = self.ssh.run_supervisorctl_status()
        found = re.findall(r'^((?!RUNNING).)*$', status.strip(), re.MULTILINE)
        not_running = len(found)

        return "check supervisorctl status", not not_running, {'not RUNNING': not_running}

    def check_errors_in_syslog(self, *_args, **_kwargs):
        errors = self.ssh.find_errors_in_syslog()
        found = len(errors.strip())

        return "check errors in syslog", not found, {'syslog errors': found}

    def check_errors_in_install_log(self, *_args, **_kwargs):
        errors = self.ssh.find_errors_in_install_log()
        found = len(errors.strip())

        return "check errors in install.log", not found, {'install.log errors': found}