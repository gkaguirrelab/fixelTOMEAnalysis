# This makes a container for the gear. Replace the first path next to the second COPY function 
# below with a path to your local compiled matlab function

FROM ubuntu:latest
MAINTAINER Ozzy(ozenctaskin@hotmail.com)

#Copy everything into a container 
ENV FLYWHEEL /flywheel/v0/
RUN mkdir -p ${FLYWHEEL}
COPY manifest.json run ${FLYWHEEL}
COPY roi_tractography.py ${FLYWHEEL}/roi_tractography.py
COPY fslinstaller.py /fslinstaller.py
RUN chmod +x /flywheel/v0/run
RUN chmod +x ${FLYWHEEL}/croi_tractography.py

# Install required packages     
RUN apt-get update \
    && apt-get install -y \
    software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update
RUN apt-get install -y \
    wget \
    zip \
    unzip \
    git \
    cmake

# Install trekker
RUN git clone https://github.com/dmritrekker/trekker
RUN cd /trekker/; bash build_Linux.sh

# Install Anaconda
RUN wget https://repo.anaconda.com/archive/Anaconda3-2020.02-Linux-x86_64.sh
RUN bash Anaconda3-2020.02-Linux-x86_64.sh -b -p /anaconda3
ENV PATH=$PATH:/anaconda3/bin
RUN pip3 install fury, dipy

# Set the entrypoint  
ENTRYPOINT /flywheel/v0/run