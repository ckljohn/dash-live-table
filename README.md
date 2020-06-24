# Dash Live Table Poc

## Setup

1. Start ES and dash application
   ```shell script
   docker-compose up --build
   ```
1. Wait until ES is ready
1. Stream tcpdump into ES (require root access)
   ```shell script
   sudo python mock_stream.py
   ``` 
1. Go to http://localhost:5000/dash-apps/tcpdump/
