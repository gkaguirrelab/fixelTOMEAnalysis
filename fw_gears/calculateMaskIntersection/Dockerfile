# This makes a container for the gear. Replace the first path next to the second COPY function 
# below with a path to your local compiled matlab function

FROM neurodebian:xenial
MAINTAINER Ozzy(ozenctaskin@hotmail.com)

#Copy everything into a container 
ENV FLYWHEEL /flywheel/v0/
RUN mkdir -p ${FLYWHEEL}
COPY manifest.json run ${FLYWHEEL}
COPY calculateMaskIntersection.py ${FLYWHEEL}/calculateMaskIntersection.py
COPY fslinstaller.py /fslinstaller.py
RUN chmod +x /flywheel/v0/run
RUN chmod +x ${FLYWHEEL}/calculateMaskIntersection.py

# Install required packages     
RUN apt-get update \
    && apt-get install -y \
    software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update
RUN apt-get install -y \
    build-essential \
    wget \
    zip \
    python \
    unzip \
    git \
    cmake \
    libgl1-mesa-glx 

# Install python2 for fslinstallation and install the newest verison of fsl
RUN apt-get install python -y
RUN python2 /fslinstaller.py -d /fsl 

# Install Anaconda
RUN apt-get install wget
RUN wget https://repo.anaconda.com/archive/Anaconda3-2020.02-Linux-x86_64.sh
RUN bash Anaconda3-2020.02-Linux-x86_64.sh -b -p /anaconda3
ENV PATH=$PATH:/anaconda3/bin
RUN conda update --all -y

# Set the entrypoint  
ENTRYPOINT /flywheel/v0/run



