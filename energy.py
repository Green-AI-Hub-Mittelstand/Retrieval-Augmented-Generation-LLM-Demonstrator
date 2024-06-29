import subprocess
import re

import subprocess
import re
import threading
import time

class PowerMetricsMonitor:
    def __init__(self):
        self.cpu_power = []
        self.gpu_power = []
        # If your command requires sudo without a password, make sure to configure it as mentioned earlier
        self.cmd = ["sudo", "powermetrics", "-n", "1", "--samplers", "cpu_power,gpu_power"]
        self.pattern_cpu = r'CPU Power:\s+(\d+)\s+mW'
        self.pattern_gpu = r'GPU Power:\s+(\d+)\s+mW'
        self.running = False

    def _update_power_metrics(self):
        """Run the command and update CPU and GPU power metrics."""
        try:
            output = subprocess.check_output(self.cmd, universal_newlines=True)
            cpu_match = re.search(self.pattern_cpu, output)
            gpu_match = re.search(self.pattern_gpu, output)
            if cpu_match:
                self.cpu_power.append(int(cpu_match.group(1)))
            if gpu_match:
                self.gpu_power.append(int(gpu_match.group(1)))
            del self.cpu_power[:-300]
            del self.gpu_power[:-300]

        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e}")

    def run(self):
        """Continuously check and update power metrics every second."""
        self.running = True
        while self.running:
            self._update_power_metrics()
            # Sleep for a second before next update
            time.sleep(1)

    def start(self):
        """Start the monitoring in a separate thread."""
        thread = threading.Thread(target=self.run)
        thread.start()
    
    def stop(self):
        """Stop the monitoring."""
        self.running = False