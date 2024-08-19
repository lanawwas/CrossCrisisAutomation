# MSNA Data Portal - Script 

A comprehensive setup bash script for a Dockerized development environment. It's designed to automate the deployment of a multi-service architecture, including PostgreSQL, JupyterHub, RStudio, Flask, Airflow, , using Docker Compose.

# Prerequisite: 

  - Ubuntu server
  - Docker and Docker-compose
  - Python 3.12
  - Python virtual enviroment 

# Key Points:

    - Virtual Environment Activation: The script starts by activating a Python virtual environment, which is essential for ensuring the right dependencies are used.

    - YAML Parsing: It loads configuration settings from a YAML file (config.yml) using Python, which allows for flexible configuration management.

    - Docker Secrets: The script checks and creates Docker secrets for sensitive information, like database passwords, which improves security.

    - Service Configuration: Each service (e.g., PostgreSQL, JupyterHub, RStudio, etc.) is configured within the script, including setting up Docker Compose configurations and handling dependencies.

    - JupyterHub and RStudio: The script dynamically configures JupyterHub to allow multiple users and sets up RStudio instances for users specified in the config.yml.

    - Nginx Reverse Proxy: Nginx is configured as a reverse proxy to route requests to different services, such as Flask, JupyterHub, and RStudio.

    - Flask App: The script includes a basic Flask application setup, demonstrating how custom services can be integrated into the environment.

    - Command-line Handling: The script provides an interface for installing, updating, and uninstalling the services, making it easier to manage the environment.

How to Run:

    Customize the config.yml File: Ensure that the file has the correct number of users and corresponding configurations.
    Activate Virtual Environment: Ensure the Python virtual environment is activated.
    Run the Script: Use ./setup_data_platform.sh install to install and configure the platform.
