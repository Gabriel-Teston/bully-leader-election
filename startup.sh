# Install or update needed software
apt-get update
apt-get install -yq git supervisor python3-pip python3-venv jq

# Fetch source code
mkdir /opt/app
git clone https://github.com/Gabriel-Teston/bully-leader-election.git /opt/app

# Python environment setup
python3 -m venv /opt/app/env
pip3 install -r /opt/app/requirements.txt

export INSTACES=$(sudo curl "http://metadata.google.internal/computeMetadata/v1/project/attributes/" -H "Metadata-Flavor: Google")

# Start application
cd /opt/app/
flask --app=server run --host=0.0.0.0 --port=80
echo "" > sudo tee /DONE