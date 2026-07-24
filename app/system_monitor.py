import psutil

_last_net = psutil.net_io_counters()

def get_system_stats() -> dict:
    global _last_net

    cpu_percent = psutil.cpu_percent(interval=0.3)
    mem = psutil.virtual_memory()

    current_net = psutil.net_io_counters()
    bytes_sent_delta = current_net.bytes_sent - _last_net.bytes_sent
    bytes_recv_delta = current_net.bytes_recv - _last_net.bytes_recv
    _last_net = current_net

    network_kbps = round((bytes_sent_delta + bytes_recv_delta) / 1024, 2)

    return {
        "cpu_percent": round(cpu_percent, 1),
        "mem_used_mb": round(mem.used / (1024 * 1024), 1),
        "mem_total_mb": round(mem.total / (1024 * 1024), 1),
        "mem_percent": round(mem.percent, 1),
        "network_kbps": network_kbps,
    }