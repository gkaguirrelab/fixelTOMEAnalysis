# This makes a container for the gear. Replace the first path next to the second COPY function 
# below with a path to your local compiled matlab function

FROM neurodebian:xenial
MAINTAINER Ozzy(ozenctaskin@hotmail.com)

#Copy everything into a container 
ENV FLYWHEEL /flywheel/v0/
RUN mkdir -p ${FLYWHEEL}
COPY manifest.json run ${FLYWHEEL}
COPY create_fod_image.py ${FLYWHEEL}/create_fod_image.py
COPY ConstraintSet.mat ${FLYWHEEL}/ConstraintSet.mat
COPY sphere5120.obj ${FLYWHEEL}/sphere5120.obj
COPY adaptConOpt /tmp/adaptConOpt

RUN chmod +x /flywheel/v0/run
RUN chmod +x /opt/func_input/*  
RUN chmod +x ${FLYWHEEL}/create_fod_image.py

# Install required packages     
RUN apt-get update \
    && apt-get install -y \
    software-properties-common
RUN apt-get install -y \
    git \
    g++ \ 
    python \
    libeigen3-dev \
    zlib1g-dev \
    libqt5opengl5-dev \
    libqt5svg5-dev \ 
    libgl1-mesa-dev \
    libfftw3-dev \
    libtiff5-dev \
    libpng-dev \
    python3.7 \
    python3-pip \
    zip \
    unzip

# Install python packages   
RUN python3.7 -m pip install --upgrade pip
RUN pip install numpy
RUN python3.7 -m pip install 'matplotlib==3.1.3' 'nibabel==2.5.1' 'numpy==1.18.1' 'imageio==2.8.0' 'nilearn==0.6.2' 'neuropythy==0.11.5' 'pandas==1.0.3' 'hcp-utils==0.1.0'

# Install Mrtrix
RUN git clone https://github.com/MRtrix3/mrtrix3.git
RUN cd mrtrix3; ./configure; ./build

# Set the entrypoint  
ENTRYPOINT /flywheel/v0/run



