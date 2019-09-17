from .ssh import get_gpu_utils


def gpu_status(servers):
    results = []
    for server in servers:
        try:
            print("connect: " + server)
            gpu_infos, status = get_gpu_utils(server, 22,
                                              'monitor', 'monitor')
            results.append({"name": server, "gpu_infos": gpu_infos, "status": status})
        except Exception as e:
            print(e)
            pass
    return results
