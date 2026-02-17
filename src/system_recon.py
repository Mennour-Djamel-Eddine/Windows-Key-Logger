#!/usr/bin/python
# -*- coding: utf-8 -*-
import platform
import socket
import uuid
import re
import urllib.request
import subprocess
import json
import os

class SystemRecon:
    def __init__(self):
        self.info = {}

    def get_system_info(self):
        try:
            self.info['platform'] = platform.system()
            self.info['platform_release'] = platform.release()
            self.info['platform_version'] = platform.version()
            self.info['architecture'] = platform.machine()
            self.info['hostname'] = socket.gethostname()
            self.info['ip_address'] = socket.gethostbyname(socket.gethostname())
            self.info['mac_address'] = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
            self.info['processor'] = platform.processor()
            
            # Retrieve public IP address
            try:
                with urllib.request.urlopen('https://api.ipify.org', timeout=5) as response:
                    self.info['external_ip'] = response.read().decode('utf-8')
            except:
                self.info['external_ip'] = "Unavailable"
                
            # Get current user
            try:
                self.info['username'] = os.getlogin()
            except:
                self.info['username'] = "Unknown"

            return self.info
        except Exception as e:
            return {"error": str(e)}

    def get_installed_software(self):
        # Enumerate installed security software via WMI
        security_software = []
        if platform.system() == "Windows":
            try:
                # specific check for AV
                cmd = "wmic /namespace:\\\\root\\SecurityCenter2 path AntiVirusProduct get displayName /format:list"
                output = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
                for line in output.split('\n'):
                    if "displayName" in line:
                        security_software.append(line.split('=')[1].strip())
            except:
                pass
        return security_software

    def formatted_report(self):
        self.get_system_info()
        avs = self.get_installed_software()
        
        report = "="*30 + "\n"
        report += " SYSTEM RECONNAISSANCE REPORT \n"
        report += "="*30 + "\n"
        
        for key, value in self.info.items():
            report += f"{key}: {value}\n"
            
        if avs:
            report += "\nDetected Security Software:\n"
            for av in avs:
                report += f"- {av}\n"
        else:
            report += "\nNo Security Software Detected (or wmic failed)\n"
            
        report += "="*30 + "\n"
        return report

if __name__ == "__main__":
    recon = SystemRecon()
