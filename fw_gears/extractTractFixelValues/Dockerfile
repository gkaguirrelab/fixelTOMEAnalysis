# This makes a container for the gear. Replace the first path next to the second COPY function 
# below with a path to your local compiled matlab function

FROM neurodebian:xenial
MAINTAINER Ozzy(ozenctaskin@hotmail.com)

#Copy everything into a container 
ENV FLYWHEEL /flywheel/v0/
RUN mkdir -p ${FLYWHEEL}
COPY manifest.json run ${FLYWHEEL}
COPY fixelAnalysis.py ${FLYWHEEL}/fixelAnalysis.py
RUN chmod +x /flywheel/v0/run
RUN chmod +x ${FLYWHEEL}/fixelAnalysis.py

# Install required packages     
RUN apt-get update \
    && apt-get install -y \
    software-properties-common
RUN apt-get install -y \
    git \
    g++ \ 
    python \
    python-pip \
    libeigen3-dev \
    zlib1g-dev \
    libqt5opengl5-dev \
    libqt5svg5-dev \ 
    libgl1-mesa-dev \
    libfftw3-dev \
    libtiff5-dev \
    libpng-dev \
    zip \
    unzip

# Install Mrtrix
RUN apt-get install libqt4-opengl-dev -y
RUN git clone https://github.com/MRtrix3/mrtrix3.git
RUN cd mrtrix3; ./configure; ./build

# Install Anaconda
RUN apt-get install wget
RUN wget https://repo.anaconda.com/archive/Anaconda3-2020.02-Linux-x86_64.sh
RUN bash Anaconda3-2020.02-Linux-x86_64.sh -b -p /anaconda3
ENV PATH=$PATH:/anaconda3/bin
RUN conda update --all -y

# Set the entrypoint  
ENTRYPOINT /flywheel/v0/run



