#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# Activate the Python virtual environment 

source /msna/CrossCrisisAutomation/scripts/MSNADataPortal/env/bin/activate

# Load YAML parser function using Python
parse_yaml() {
   python -c "import yaml,sys; print(yaml.safe_load(sys.stdin.read())$1)" < "$2"
}

# Configuration
CONFIG_FILE="config.yml"

# Function to check if a Docker container is already running
is_container_running() {
    local container_name=$1
    if [ "$(docker ps -q -f name=${container_name})" ]; then
        echo "true"
    else
        echo "false"
    fi
}

# Function to check if Docker secret already exists
is_secret_exist() {
    local secret_name=$1
    if [ "$(docker secret ls | grep ${secret_name})" ]; then
        echo "true"
    else
        echo "false"
    fi
}

# Function to create Docker secrets if not already created
create_docker_secret() {
    local secret_name=$1
    local secret_value=$2

    if [ "$(is_secret_exist ${secret_name})" == "false" ]; then
        echo "${secret_value}" | docker secret create ${secret_name} -
    else
        echo "Docker secret '${secret_name}' already exists."
    fi
}

# Load configuration from YAML file
POSTGRES_USER=$(parse_yaml "['services']['postgres']['user']" $CONFIG_FILE)
POSTGRES_DB=$(parse_yaml "['services']['postgres']['db']" $CONFIG_FILE)
POSTGRES_PORT=$(parse_yaml "['services']['postgres']['port']" $CONFIG_FILE)
PGADMIN_DEFAULT_EMAIL=$(parse_yaml "['services']['pgadmin']['default_email']" $CONFIG_FILE)
PGADMIN_PORT=$(parse_yaml "['services']['pgadmin']['port']" $CONFIG_FILE)
JUPYTERHUB_PORT=$(parse_yaml "['services']['jupyterhub']['port']" $CONFIG_FILE)
#RSTUDIO_USER=$(parse_yaml "['services']['rstudio']['user']" $CONFIG_FILE)
RSTUDIO_BASE_PORT=$(parse_yaml "['services']['rstudio']['base_port']" $CONFIG_FILE)
AIRFLOW_PORT=$(parse_yaml "['services']['airflow']['port']" $CONFIG_FILE)
POSTGREST_PORT=$(parse_yaml "['services']['postgrest']['port']" $CONFIG_FILE)
POSTGREST_DB_SCHEMA=$(parse_yaml "['services']['postgrest']['db_schema']" $CONFIG_FILE)
POSTGREST_DB_ANON_ROLE=$(parse_yaml "['services']['postgrest']['db_anon_role']" $CONFIG_FILE)
FLASK_PORT=$(parse_yaml "['services']['flask']['port']" $CONFIG_FILE)
VSCODE_PORT=$(parse_yaml "['services']['vscode']['port']" $CONFIG_FILE)
NGINX_HTTP_PORT=$(parse_yaml "['services']['nginx']['http_port']" $CONFIG_FILE)
NGINX_HTTPS_PORT=$(parse_yaml "['services']['nginx']['https_port']" $CONFIG_FILE)
USERS=$(parse_yaml "['users']" $CONFIG_FILE)

# Placeholder for secure passwords
POSTGRES_PASSWORD="your_secure_password"
PGADMIN_DEFAULT_PASSWORD="your_secure_pgadmin_password"

# Create Docker secrets if they don't already exist
create_docker_secret "POSTGRES_PASSWORD" "${POSTGRES_PASSWORD}"
create_docker_secret "PGADMIN_DEFAULT_PASSWORD" "${PGADMIN_DEFAULT_PASSWORD}"
#create_docker_secret "RSTUDIO_PASSWORD" "${RSTUDIO_PASSWORD}"

# JupyterHub Configuration 
 generate_jupyterhub_config() {
	 mkdir -p jupyterhub
	 
	 cat <<EOF > jupyterhub/jupyterhub_config.py 
c = get_config()

# JupyterHub Configuration 
c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner' 
c.DockerSpawner.image = 'jupyter/base-notebook:latest' 
c.JupyterHub_hub_ip = 'jupyterhub'
c.JupyterHub.port = ${JUPYTERHUB_PORT}
c.JupyterHub.bind_url = 'http://:8000/'

# Predefined users
c.Authenticator.allowed_users = set([${USERS}])
EOF
}

# Generate JupyterHub configuration 
generate_jupyterhub_config

# Docker Compose configuration
generate_docker_compose() {
cat <<EOF > docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:13
    container_name: postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_DB: ${POSTGRES_DB}
    #secrets:
    #  - POSTGRES_PASSWORD
    volumes:
      - ./postgres_data:/var/lib/postgresql/data
    ports:
      - "${POSTGRES_PORT}:5432"
    networks:
      - app-network

  pgadmin:
    image: dpage/pgadmin4
    container_name: pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_DEFAULT_EMAIL}
    #secrets:
    #  - PGADMIN_DEFAULT_PASSWORD
    ports:
      - "${PGADMIN_PORT}:80"
    depends_on:
      - postgres
    networks:
      - app-network

  jupyterhub:
    image: jupyterhub/jupyterhub:latest
    container_name: jupyterhub
    volumes:
      - ./jupyterhub:/srv/jupyterhub
    ports:
      - "${JUPYTER_PORT}:8000"
    networks:
      - app-network

  rstudio:
    image: rocker/verse
    container_name: rstudio
    environment:
      USER: ${RSTUDIO_USER}
    secrets:
      - RSTUDIO_PASSWORD
    ports:
      - "${RSTUDIO_PORT}:8787"
    networks:
      - app-network

  airflow:
    image: apache/airflow:2.3.0
    container_name: airflow
    environment:
      AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql+psycopg2://${POSTGRES_USER}:@postgres:${POSTGRES_PORT}/${POSTGRES_DB}
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
    volumes:
      - ./airflow/dags:/usr/local/airflow/dags
      - ./airflow/logs:/usr/local/airflow/logs
      - ./airflow/plugins:/usr/local/airflow/plugins
    ports:
      - "${AIRFLOW_PORT}:8080"
    depends_on:
      - postgres
    networks:
      - app-network

  postgrest:
    image: postgrest/postgrest
    container_name: postgrest
    environment:
      PGRST_DB_URI: postgres://${POSTGRES_USER}:@postgres:${POSTGRES_PORT}/${POSTGRES_DB}
      PGRST_DB_SCHEMA: ${POSTGREST_DB_SCHEMA}
      PGRST_DB_ANON_ROLE: ${POSTGREST_DB_ANON_ROLE}
    ports:
      - "${POSTGREST_PORT}:3000"
    depends_on:
      - postgres
    networks:
      - app-network

  vscode
    image: codercom/code-server:latest
    container_name: vscode
    environment: 
 	PASSWORD: test
    volumes: 
	- "${VSCODE_PORT}:8443"
    networks: 
	-app-network

  flask:
    image: flask_app_image  # Placeholder; replace with actual Docker image
    container_name: flask
    build:
      context: ./flask_app  # Directory containing Flask app Dockerfile
    ports:
      - "${FLASK_PORT}:5000"
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    container_name: nginx
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "${NGINX_HTTP_PORT}:80"
      - "${NGINX_HTTPS_PORT}:443"
    depends_on:
      - jupyterhub
      - vscode
      - airflow
      - postgrest
      - flask
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

#secrets:
#  POSTGRES_PASSWORD:
#    external: true
#  PGADMIN_DEFAULT_PASSWORD:
#    external: true
#  RSTUDIO_PASSWORD:
#    external: true
EOF

# Add Rstudio services
  port_offest=0 
  for user in $(parse_yaml "['users']" $CONFIG_FILE); do 
    cat << EOF >> docker-compose.yml 
  rstudio_${user}:
    image: rocker/rstudio:latest
    container_name: rstudio_${user}
    enviroment: 
	USER: ${user} 
    ports: 
	- "$((RSTUDIO_BASE_PORT + port_offset)):8787"
    depends_on: 
	- postgres
    networks: 
	- app-network 
EOF
    port_offset=$((port_offset +1))
done 

}

# Generate Docker Compose file
generate_docker_compose

# NGINX configuration
generate_nginx_conf() {
mkdir -p nginx

cat <<EOF > nginx/nginx.conf
user  nginx;
worker_processes  1;

error_log  /var/log/nginx/error.log warn;
pid        /var/run/nginx.pid;

events {
    worker_connections  1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    log_format  main  '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                      '\$status \$body_bytes_sent "\$http_referer" '
                      '"\$http_user_agent" "\$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile        on;
    keepalive_timeout  65;

    include /etc/nginx/conf.d/*.conf;

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://flask:5000;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        location /jupyter {
            proxy_pass http://jupyter:8888;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        location /rstudio {
            proxy_pass http://rstudio:8787;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        location /airflow {
            proxy_pass http://airflow:8080;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        location /api {
            proxy_pass http://postgrest:3000;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
    }
}
EOF
}

# Generate NGINX configuration file
generate_nginx_conf

# Flask app Docker setup
generate_flask_app() {
mkdir -p flask_app

cat <<EOF > flask_app/Dockerfile
FROM python:3.8-slim

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

CMD ["python", "app.py"]
EOF

cat <<EOF > flask_app/requirements.txt
Flask==2.0.2
EOF

cat <<EOF > flask_app/app.py
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

if __name__ == "__main__":
    app.run(host='0.0.0.0')
EOF
}

# Generate Flask app files
generate_flask_app

# Function to start the Docker Compose services
start_services() {
    docker-compose up -d
}

# Function to stop and remove Docker Compose services
stop_services() {
    docker-compose down --volumes
}

# Function to uninstall services
uninstall_services() {
    stop_services
    rm -rf postgres_data nginx flask_app notebooks datasets airflow
    echo "All services and data have been removed."
}

# Command-line argument handling
case "$1" in
    install)
        if [ "$(is_container_running 'postgres')" == "true" ]; then
            echo "Services are already running. Use 'update' to make changes or 'uninstall' to remove them."
            exit 0
        fi
        start_services
        echo "Infrastructure setup complete. Visit your server's IP address to access the services."
        ;;
    update)
        start_services
        echo "Services updated and running."
        ;;
    uninstall)
        uninstall_services
        ;;
    *)
        echo "Usage: $0 {install|update|uninstall}"
        exit 1
        ;;
esac
