import time

import GPUtil
import psutil
from prometheus_client import Counter
from prometheus_client import Gauge
from prometheus_client import start_http_server


class PrometheusMetrics:
    """Defines the promethus metrics and populates them with relevant values."""

    def __init__(self):
        """Initialize the metrics we want to measure."""
        self.cpu_average_gauge = Gauge("cpu", "Description of gauge")
        self.cpu_temp_gauge = Gauge("cpu_temperature", "Description of gauge")
        self.ram_gauge = Gauge("ram", "Description of gauge")
        self.swap_gauge = Gauge("swap", "Description of gauge")

        self.harddisk_gauge = Gauge("harddisk", "Avaiable harddisk space")
        self.uptime_gauge = Counter("uptime", "Description of gauge")

        self.gpu_average_gauge = Gauge("gpu", "Description of gauge").set(0.0)
        self.gpu_memory_gauge = Gauge("gpu_memory", "Description of gauge").set(0.0)
        self.gpu_temp_gauge = Gauge("gpu_temperature", "Description of gauge").set(0.0)

    def seconds_elapsed(self) -> float:
        """Function to calculate uptime.

        Returns:
            float: time elapsed since system boot
        """
        return time.time() - psutil.boot_time()

    def update_metrics(self):
        """Updates the metrics defined in the init function."""
        self.ram_gauge.set(psutil.virtual_memory().percent)
        self.swap_gauge.set(psutil.swap_memory().percent)
        self.cpu_average_gauge.set(psutil.cpu_percent(interval=1, percpu=False))
        self.cpu_temp_gauge.set(psutil.sensors_temperatures().get("acpitz")[0].current)
        self.harddisk_gauge.set(psutil.disk_usage("/").percent)
        self.uptime_gauge.inc(self.seconds_elapsed())

        try:
            # TODO: Test this
            gpu = GPUtil.getGPUs()[0]
            self.gpu_average_gauge.set(gpu.load * 100)
            self.gpu_memory_gauge.set(gpu.memoryUtil * 100)
            self.gpu_temp_gauge.set(gpu.temp_gpu)
        except Exception:
            pass  # Device does not have a Nvida GPU


if __name__ == "__main__":
    # Start up the server to expose the metrics.
    start_http_server(8000)
    metrics = PrometheusMetrics()
    while True:
        # Prometheus default scrape time is 5 seconds. We might as well use the same value.
        time.sleep(5)
        metrics.update_metrics()
