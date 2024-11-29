### Setup the Git Repository Locally
```bash

git clone https://github.com/manavneema/wdps_group27.git
```

### Run the following:
```
cd wdps_group27
docker run -it -v ./:/home/user/app/ karmaresearch/wdps2
```

### Inside the container follow the below steps:
```bash
cd app
python -m venv venv
source venv/bin/activate

chmod +x setup.sh
./setup.sh
pip3 install -r requirements.txt
python3 entitylinker.py input.txt
```


