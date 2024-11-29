There's two ways to run the code:

1. Using publicly hosted docker image
a. Run the following:

docker pull --platform linux/arm64 42bitstogo/entitylinker
docker run -it --platform linux/arm64 42bitstogo/entitylinker

b. Run the following in the container:
python EntityExtractionAndLinking.py

Also attached is the file with the code: EntityExtractionAndLinking.py.
This code might take varying time to run depending on the machine. 



2. Using the existing docker image given for the original assignment and following the below steps:
a. Run the following commands:
apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    cmake \
    pkg-config \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

b. pip3 install --upgrade pip setuptools wheel --no-cache-dir \
    && pip3 install --prefer-binary spacy --no-cache-dir

c. Copy the requirements from the given requirements.txt and then run:
pip3 install -r requirements.txt --no-cache-dir

d. Run the following:
python -m spacy download en_core_web_md

e. Finally you can run the python script to open the interactive shell:
python EntityExtractionAndLinking.py

All instructions would now be visible on the screen. You can ask the LLM a question and it would answer along with finding the entities and linking the entities. 


