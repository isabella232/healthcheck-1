import re

from healthcheck.check_suites.base_suite import BaseCheckSuite, load_params
from healthcheck.common_funcs import GB, to_gb, to_kops


class ClusterChecks(BaseCheckSuite):
    """Cluster"""

    def __init__(self, _config):
        super().__init__(_config)
        self.params = load_params('cluster')

    def _check_connectivity(self):
        self._check_api_connectivity()

    def check_license_shards_limit(self, *_args, **_kwargs):
        """check shards limit in license"""
        number_of_shards = self.api.get_number_of_values('shards')
        match = re.search(r'Shards limit : (\d+)\n', self.api.get('license')['license'], re.MULTILINE | re.DOTALL)
        shards_limit = int(match.group(1))

        result = shards_limit >= number_of_shards
        kwargs = {'shards limit': shards_limit, 'number of shards': number_of_shards}
        return result, kwargs

    def check_license_expired(self, *_args, **_kwargs):
        """check if license is expired"""
        expired = self.api.get('license')['expired']

        return not expired, {'license expired': expired}

    def check_number_of_shards(self, *_args, **_kwargs):
        """check if enough shards"""
        number_of_shards = self.api.get_number_of_values('shards')

        if not _kwargs:
            return None, {'number of shards': number_of_shards}, "get number of shards"

        result = number_of_shards >= _kwargs['min_shards']
        kwargs = {'number of shards': number_of_shards, 'min shards': _kwargs['min_shards']}
        return result, kwargs

    def check_number_of_nodes(self, *_args, **_kwargs):
        """check if enough nodes"""
        number_of_nodes = self.api.get_number_of_values('nodes')

        if not _kwargs:
            return None, {'number of nodes': number_of_nodes}, "get number of nodes"

        result = number_of_nodes >= _kwargs['min_nodes'] and number_of_nodes % 2 != 0
        kwargs = {'number of nodes': number_of_nodes, 'min nodes': _kwargs['min_nodes']}
        return result, kwargs

    def check_number_of_cores(self, *_args, **_kwargs):
        """check if enough cores"""
        number_of_cores = self.api.get_sum_of_values('nodes', 'cores')

        if not _kwargs:
            return None, {'number of cores': number_of_cores}, "get number of cores"

        result = number_of_cores >= _kwargs['min_cores']
        kwargs = {'number of cores': number_of_cores, 'min cores': _kwargs['min_cores']}
        return result, kwargs

    def check_total_memory(self, *_args, **_kwargs):
        """check if enough RAM"""
        total_memory = self.api.get_sum_of_values('nodes', 'total_memory')

        if not _kwargs:
            return None, {'total memory': '{} GB'.format(to_gb(total_memory))}, "get total memory"

        result = total_memory >= _kwargs['min_memory'] * GB
        kwargs = {'total memory': '{} GB'.format(to_gb(total_memory)), 'min memory': '{} GB'.format(_kwargs['min_memory'])}
        return result, kwargs

    def check_ephemeral_storage(self, *_args, **_kwargs):
        """check if enough ephemeral storage"""
        epehemeral_storage_size = self.api.get_sum_of_values('nodes', 'ephemeral_storage_size')

        if not _kwargs:
            return None, {'ephemeral storage size': '{} GB'.format(to_gb(epehemeral_storage_size))}, "get ephemeral storage size"

        result = epehemeral_storage_size >= _kwargs['min_ephemeral_storage'] * GB
        kwargs = {'ephemeral storage size': '{} GB'.format(to_gb(epehemeral_storage_size)),
                  'min ephemeral size': '{} GB'.format(_kwargs['min_ephemeral_storage'])}
        return result, kwargs

    def check_persistent_storage(self, *_args, **_kwargs):
        """check if enough persistent storage"""
        persistent_storage_size = self.api.get_sum_of_values('nodes', 'persistent_storage_size')

        if not _kwargs:
            return None, {'persistent storage size': '{} GB'.format(to_gb(persistent_storage_size))}, "get persistent storage size"

        result = persistent_storage_size >= _kwargs['min_persistent_storage'] * GB
        kwargs = {'persistent storage size': '{} GB'.format(to_gb(persistent_storage_size)),
                  'min persistent size': '{} GB'.format(_kwargs['min_persistent_storage'] )}
        return result, kwargs

    def check_throughput(self, *_args, **_kwargs):
        """get throughput"""
        kwargs = {}
        stats = self.api.get('cluster/stats')

        # calculate minimum
        min_total_req = min([i['total_req'] for i in filter(lambda x: x.get('total_req'), stats['intervals'])])

        # calculate average
        total_reqs = list(filter(lambda x: x.get('total_req'), stats['intervals']))
        sum_total_req = sum([i['total_req'] for i in total_reqs])
        avg_total_req = sum_total_req / len(total_reqs)

        # calculate maximum
        max_total_req = max([i['total_req'] for i in filter(lambda x: x.get('total_req'), stats['intervals'])])

        kwargs['minimum'] = '{} Kops/sec'.format(to_kops(min_total_req))
        kwargs['average'] = '{} Kops/sec'.format(to_kops(avg_total_req))
        kwargs['maximum'] = '{} Kops/sec'.format(to_kops(max_total_req))

        return None, kwargs

    def check_memory_usage(self, *_args, **_kwargs):
        """get memory usage"""
        kwargs = {}
        stats = self.api.get('cluster/stats')

        # calculate minimum
        min_free_mem = min(i['free_memory'] for i in filter(lambda x: x.get('free_memory'), stats['intervals']))

        # calculate average
        free_mems = list(filter(lambda x: x.get('free_memory'), stats['intervals']))
        sum_free_mem = sum(i['free_memory'] for i in free_mems)
        avg_free_mem = sum_free_mem/len(free_mems)

        # calculate maximum
        max_free_mem = max(i['free_memory'] for i in filter(lambda x: x.get('free_memory'), stats['intervals']))

        total_mem = self.api.get_sum_of_values('nodes', 'total_memory')

        kwargs['minimum'] = '{} GB'.format(to_gb(total_mem - max_free_mem))
        kwargs['average'] = '{} GB'.format(to_gb(total_mem - avg_free_mem))
        kwargs['maximum'] = '{} GB'.format(to_gb(total_mem - min_free_mem))

        return None, kwargs

    def check_ephemeral_storage_usage(self, *_args, **_kwargs):
        """get ephemeral storage usage"""
        kwargs = {}
        stats = self.api.get('cluster/stats')

        # calculate minimum
        minimum = min([i['ephemeral_storage_avail'] for i in
                       filter(lambda x: x.get('ephemeral_storage_avail'), stats['intervals'])])

        # calculate average
        ephemeral_storage_avails = list(filter(lambda x: x.get('ephemeral_storage_avail'), stats['intervals']))
        sum_ephemeral_storage_avail = sum(i['ephemeral_storage_avail'] for i in ephemeral_storage_avails)
        average = sum_ephemeral_storage_avail / len(ephemeral_storage_avails)

        # calculate maximum
        maximum = max([i['ephemeral_storage_avail'] for i in
                       filter(lambda x: x.get('ephemeral_storage_avail'), stats['intervals'])])

        ephemeral_storage_size = self.api.get_sum_of_values(f'nodes', 'ephemeral_storage_size')

        kwargs['minimum'] = '{} GB'.format(to_gb(ephemeral_storage_size - maximum))
        kwargs['average'] = '{} GB'.format(to_gb(ephemeral_storage_size - average))
        kwargs['maximum'] = '{} GB'.format(to_gb(ephemeral_storage_size - minimum))

        return None, kwargs

    def check_persistent_storage_usage(self, *_args, **_kwargs):
        """get persistent storage usage"""
        kwargs = {}
        stats = self.api.get('cluster/stats')

        # calculate minimum
        minimum = min([i['persistent_storage_avail'] for i in
                       filter(lambda x: x.get('persistent_storage_avail'), stats['intervals'])])

        # calculate average
        persistent_storage_avails = list(filter(lambda x: x.get('persistent_storage_avail'), stats['intervals']))
        sum_persistent_storage_avail = sum(i['persistent_storage_avail'] for i in persistent_storage_avails)
        average = sum_persistent_storage_avail / len(persistent_storage_avails)

        # calculate maximum
        maximum = max([i['persistent_storage_avail'] for i in
                       filter(lambda x: x.get('persistent_storage_avail'), stats['intervals'])])

        persistent_storage_size = self.api.get_sum_of_values(f'nodes', 'persistent_storage_size')

        kwargs['minimum'] = '{} GB'.format(to_gb(persistent_storage_size - maximum))
        kwargs['average'] = '{} GB'.format(to_gb(persistent_storage_size - average))
        kwargs['maximum'] = '{} GB'.format(to_gb(persistent_storage_size - minimum))

        return None, kwargs
