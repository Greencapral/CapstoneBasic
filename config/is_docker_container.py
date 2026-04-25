import os
import socket
import re

def is_docker_container():
    return os.getenv("ENVIRONMENT") == "docker"