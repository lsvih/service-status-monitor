# -*- coding: utf-8 -*-
import xml.etree.ElementTree

import paramiko


def remove_values_from_list(the_list, val):
    return [value for value in the_list if value != val]


def owner(ssh, pid):
    try:
        # the /proc/PID is owned by process creator
        # pid_query = "ps --pid " + str(pid) + " -u"
        pid_query = "ps --pid {} -o pid,user:20,%cpu,%mem,command --no-headers".format(pid)
        # get UID via stat call
        stdin, stdout, stderr = ssh.exec_command(pid_query)
        # look up the username from uid
        pid_out = stdout.read()
        if isinstance(pid_out, bytes):
            pid_out = pid_out.decode()
        pid_out = pid_out.strip().split(" ")
        pid_out = remove_values_from_list(pid_out, "")
        username = pid_out[1].strip()
        command = " "
        for index in range(4, len(pid_out)):
            command += pid_out[index].strip()
            command += " "
    except Exception as e:
        username = 'unknown'
        command = 'unknown'
        print (e)
    return username, command


def get_server_status(hostname, port, username, password):
    # 创建SSH对象
    ssh = paramiko.SSHClient()

    # 把要连接的机器添加到known_hosts文件中
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # 连接服务器
    ssh.connect(hostname=hostname, port=port, username=username, password=password)

    # cmd = 'ps'
    # cmd = 'ls -l;ifconfig'  # 多个命令用;隔开
    # 获取cpu使用率
    cmd = "top -b -d1 -n5|grep -i \"Cpu(s)\""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    cpu_usage_datas = stdout.read()
    cpu_usage_datas = cpu_usage_datas.split("\n")
    cpu_usage_datas.pop()
    cpu_usage = []
    for cpu_usage_data in cpu_usage_datas:
        # print(cpu_usage_data)
        cpu_usage_data = cpu_usage_data[cpu_usage_data.find(" ") + 1:cpu_usage_data.find("us") - 1]
        cpu_usage.append(float(cpu_usage_data))
    # print(cpu_usage)
    print("Cpu -usage: %0.2f %%" % max(cpu_usage))

    # 获取内存使用率
    cmd = "free -m"  # free + buff/cache
    stdin, stdout, stderr = ssh.exec_command(cmd)
    mem_usage = stdout.read()
    # print(mem_usage)
    mem_usage = mem_usage[mem_usage.find("Mem:") + 4:mem_usage.find("\n", mem_usage.find("Mem:") + 4)]
    mem_usage = mem_usage.split()
    mem_usage = map(int, mem_usage)
    mem_usage_num = (mem_usage[0] - (mem_usage[2] + mem_usage[4])) / float(mem_usage[0])
    # print(mem_usage)
    print("Mem -usage: %0.2f %%" % (mem_usage_num * 100))

    # 获取gpu使用率
    print("Gpu -usage:")
    CMD1 = 'nvidia-smi| grep MiB | grep -v Default | cut -c 4-8'
    CMD2 = 'nvidia-smi -L'
    CMD3 = 'nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits'

    stdin, stdout, stderr = ssh.exec_command(CMD2)
    gpu_info = stdout.read()
    if isinstance(gpu_info, bytes):
        gpu_info = gpu_info.decode()
    gpu_info.strip().split('\n')

    total_gpu = len(gpu_info)

    # first choose the free gpus
    stdin, stdout, stderr = ssh.exec_command(CMD1)
    gpu_usage = set(map(lambda x: int(x), stdout.read().split()))
    print(gpu_usage)
    free_gpus = set(range(total_gpu)) - gpu_usage

    # then choose the most memory free gpus
    stdin, stdout, stderr = ssh.exec_command(CMD3)
    gpu_free_mem = list(map(lambda x: int(x), stdout.read().split()))
    gpu_sorted = list(sorted(range(total_gpu), key=lambda x: gpu_free_mem[x], reverse=True))[len(free_gpus):]

    res = list(free_gpus) + list(gpu_sorted)

    print(res)

    result = stdout.read()

    if not result:
        result = stderr.read()
    ssh.close()

    print(result)


def get_gpu_utils(hostname, port, username, password):
    ssh = paramiko.SSHClient()

    # 把要连接的机器添加到known_hosts文件中
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # 连接服务器
    ssh.connect(hostname=hostname, port=port, username=username, password=password)

    # 获取gpu信息
    smi_cmd = 'nvidia-smi -q -x'  # get XML output
    stdin, stdout, stderr = ssh.exec_command(smi_cmd)
    smi_out = stdout.read()

    # 获取gpu使用率
    gpu_info_cmd = "nvidia-smi " \
                   "--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu " \
                   "--format=csv,noheader"

    stdin, stdout, stderr = ssh.exec_command(gpu_info_cmd)
    out = stdout.read()
    if isinstance(out, bytes):
        out = out.decode()
    gpu_infos = out.strip().split('\n')
    gpu_infos = map(lambda x: x.split(', '), gpu_infos)
    gpu_infos = [{'index': x[0],
                  'name': x[1],
                  'mem_total': x[2],
                  'mem_used': x[3],
                  'mem_free': x[4],
                  'gpu_util': x[5],
                  'gpu_temp': x[6],
                  }
                 for x in gpu_infos]

    e = xml.etree.ElementTree.fromstring(smi_out)
    status = {}
    for id, gpu in enumerate(e.findall('gpu')):
        gpu_stat = {}

        index = int(gpu_infos[id]['index'])
        utilization = gpu.find('utilization')
        gpu_util = utilization.find('gpu_util').text
        mem_free = gpu_infos[id]['mem_free'].split()[0]
        mem_total = gpu_infos[id]['mem_total'].split()[0]
        mem_used = gpu_infos[id]['mem_used'].split()[0]
        gpu_temp = gpu_infos[id]['gpu_temp'].split()[0]

        gpu_stat['gpu_util'] = float(gpu_util.split()[0]) / 100
        gpu_stat['mem_free'] = int(mem_free)
        gpu_stat['mem_total'] = int(mem_total)
        gpu_stat['mem_used'] = int(mem_used)
        gpu_stat['gpu_temp'] = int(gpu_temp)

        gpu_procs = []
        procs = gpu.find('processes')
        for procinfo in procs.iter('process_info'):
            pid = int(procinfo.find('pid').text)
            mem = procinfo.find('used_memory').text
            mem_num = int(mem.split()[0])
            user, command = owner(ssh, pid)
            tmp = {
                'user': user,
                'mem': mem_num,
                'command': command
            }
            gpu_procs.append(tmp)
        gpu_stat['proc'] = gpu_procs
        status[index] = gpu_stat
    ssh.close()
    return gpu_infos, status


def pretty_print(status, verbose=False):
    out_message = ""
    for id, stats in status.iteritems():
        mem_free = stats['mem_free']
        color_out = '\x1b[0m'
        color_in = color_out
        if mem_free > 10000:
            color_in = '\x1b[0;32m'
        elif mem_free > 5000:
            color_in = '\x1b[0;36m'

        # GPU的每一个列
        header = 'gpu {}: {}%, freeMEM {}{}{}/{} MiB'.format(id,
                                                             int(100 * stats['gpu_util']),
                                                             color_in,
                                                             stats['mem_free'],
                                                             color_out,
                                                             stats['mem_total'])
        # print header
        out_message += header + "\n"
        # 对应列中的线程
        for proc in stats['proc']:
            line = '{} - {} MiB'.format(proc['user'], proc['mem'])
            out_message += line + "\n"
            if verbose:
                # print(proc['command'])
                out_message += proc['command'] + "\n\n"
                # print('')
        length = len(header)
        out_message += '-' * length + "\n"
    print (out_message)
    return out_message
